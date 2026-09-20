"""
================================================================================
Módulo: exif_models.py
Descrição: Modelos de dados, agrupamento de categorias, formatação e estado
           para a tela unificada de comparação e cópia de metadados EXIF.
================================================================================
"""

import os
from datetime import datetime
from PIL import Image, ExifTags


EXIF_CATEGORIES = {
    "Imagem": [
        "ImageWidth", "ImageLength", "BitsPerSample", "Compression",
        "PhotometricInterpretation", "Orientation", "SamplesPerPixel",
        "PlanarConfiguration", "YCbCrSubSampling", "YCbCrPositioning",
        "XResolution", "YResolution", "ResolutionUnit"
    ],
    "Câmera": [
        "Make", "Model", "Software", "DateTime", "Artist", "Copyright"
    ],
    "Exposição": [
        "ExposureTime", "FNumber", "ExposureProgram", "SpectralSensitivity",
        "ISOSpeedRatings", "OECF", "ShutterSpeedValue", "ApertureValue",
        "BrightnessValue", "ExposureBiasValue", "MaxApertureValue",
        "SubjectDistance", "MeteringMode", "LightSource", "Flash",
        "FocalLength", "SubjectArea", "MakerNote", "UserComment",
        "SubsecTime", "SubsecTimeOriginal", "SubsecTimeDigitized",
        "FlashEnergy", "SpatialFrequencyResponse", "FocalLengthIn35mmFilm"
    ],
    "Data/Hora": [
        "DateTimeOriginal", "DateTimeDigitized", "OffsetTime",
        "OffsetTimeOriginal", "OffsetTimeDigitized"
    ],
    "GPS": [
        "GPSVersionID", "GPSLatitudeRef", "GPSLatitude", "GPSLongitudeRef",
        "GPSLongitude", "GPSAltitudeRef", "GPSAltitude", "GPSTimeStamp",
        "GPSSatellites", "GPSStatus", "GPSMeasureMode", "GPSDOP",
        "GPSSpeedRef", "GPSSpeed", "GPSTrackRef", "GPSTrack",
        "GPSImgDirectionRef", "GPSImgDirection", "GPSMapDatum",
        "GPSDestLatitudeRef", "GPSDestLatitude", "GPSDestLongitudeRef",
        "GPSDestLongitude", "GPSDestBearingRef", "GPSDestBearing",
        "GPSDestDistanceRef", "GPSDestDistance", "GPSProcessingMethod",
        "GPSAreaInformation", "GPSDateStamp", "GPSDifferential"
    ],
    "Outros": []
}


def format_exif_value(value):
    """Retorna uma representação em string legível e concisa para o valor da tag EXIF."""
    if value is None:
        return "—"
    if isinstance(value, bytes):
        try:
            decoded = value.decode("utf-8", errors="ignore").strip().replace("\x00", "")
            return decoded if decoded else f"<{len(value)} bytes>"
        except Exception:
            return f"<{len(value)} bytes>"
    if isinstance(value, tuple):
        # Trata coordenadas GPS ou frações
        if len(value) == 2 and isinstance(value[0], int) and isinstance(value[1], int) and value[1] != 0:
            val = value[0] / value[1]
            return f"{val:.4f}".rstrip("0").rstrip(".") if abs(val) < 1 else f"{val:.2f}".rstrip("0").rstrip(".")
        if len(value) <= 4:
            return ", ".join(str(v) for v in value)
        return f"({len(value)} itens)"
    return str(value).strip()


class ImageCardInfo:
    """Armazena informações descritivas e metadados de uma imagem carregada."""

    def __init__(self, key: str, viewer):
        self.key = key  # "A", "B", ou "C"
        self.title = f"Imagem {key}"
        self.viewer = viewer
        self.file_path = getattr(viewer, "file_path", "")
        self.file_name = os.path.basename(self.file_path) if self.file_path else "Sem arquivo"
        self.orig_size = getattr(viewer, "orig_size", (0, 0))
        self.has_exif = False
        self.exif_data = {}  # {tag_name: raw_value}
        self.file_date_str = ""
        self.thumbnail_image = None
        self._load_details()

    def _load_details(self):
        if not self.file_path or not os.path.exists(self.file_path):
            return

        # Data do arquivo
        try:
            mtime = os.path.getmtime(self.file_path)
            self.file_date_str = datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        except Exception:
            self.file_date_str = "—"

        # Leitura EXIF via Pillow
        try:
            with Image.open(self.file_path) as img:
                info = img._getexif()
                if info:
                    for tag_id, val in info.items():
                        decoded_tag = ExifTags.TAGS.get(tag_id, str(tag_id))
                        self.exif_data[decoded_tag] = val
                    self.has_exif = bool(self.exif_data)
        except Exception:
            self.has_exif = False

        # Geração de miniatura proporcional sem distorção (max 100x75)
        try:
            with Image.open(self.file_path) as img:
                thumb = img.copy()
                thumb.thumbnail((110, 75), Image.Resampling.LANCZOS)
                self.thumbnail_image = thumb
        except Exception:
            self.thumbnail_image = None


class ExifRowState:
    """Estado de configuração de cópia para uma tag EXIF individual."""

    def __init__(self, tag_name: str, available_keys: list):
        self.tag_name = tag_name
        self.available_keys = list(available_keys)  # ex: ["A", "B"] ou ["A", "B", "C"]
        self.selected = False
        self.source = ""  # "", "A", "B", ou "C"
        self.destinations = set()  # subconjunto de available_keys excluindo a source


class ExifCompareState:
    """Gerenciador central do estado comparativo da tabela EXIF."""

    def __init__(self, card_infos: dict):
        # card_infos: {"A": ImageCardInfo, "B": ImageCardInfo, ...}
        self.card_infos = card_infos
        self.keys = list(card_infos.keys())  # ["A", "B"] ou ["A", "B", "C"]
        self.all_tags = self._collect_all_tags()
        self.categories = self._build_categorized_tags()
        self.row_states = {tag: ExifRowState(tag, self.keys) for tag in self.all_tags}

    def _collect_all_tags(self):
        tags = set()
        for card in self.card_infos.values():
            tags.update(card.exif_data.keys())
        return tags

    def _build_categorized_tags(self):
        categorized = {}
        categorized_tags_set = set()

        for cat_name, cat_tags in EXIF_CATEGORIES.items():
            if cat_name == "Outros":
                continue
            cat_list = [t for t in cat_tags if t in self.all_tags]
            if cat_list:
                categorized[cat_name] = cat_list
                categorized_tags_set.update(cat_list)

        # Tags em Outros
        remaining = [t for t in sorted(self.all_tags) if t not in categorized_tags_set]
        if remaining:
            categorized["Outros"] = remaining

        return categorized

    def get_tag_values(self, tag_name: str):
        """Retorna dicionário {key: formatted_string_value} para a tag."""
        res = {}
        for key, card in self.card_infos.items():
            if tag_name in card.exif_data:
                res[key] = format_exif_value(card.exif_data[tag_name])
            else:
                res[key] = "—"
        return res

    def are_values_equal(self, tag_name: str):
        """Retorna True se todos os valores existentes para a tag forem iguais."""
        vals = []
        for card in self.card_infos.values():
            if tag_name in card.exif_data:
                vals.append(format_exif_value(card.exif_data[tag_name]))
        if not vals:
            return True
        return all(v == vals[0] for v in vals)

    def is_tag_different(self, tag_name: str):
        """Retorna True se a tag existir em pelo menos duas imagens e tiver valores distintos."""
        vals = []
        for card in self.card_infos.values():
            if tag_name in card.exif_data:
                vals.append(format_exif_value(card.exif_data[tag_name]))
        return len(vals) >= 2 and not all(v == vals[0] for v in vals)

    def is_present_in_all(self, tag_name: str):
        """Retorna True se a tag estiver presente em todas as imagens carregadas."""
        return all(tag_name in card.exif_data for card in self.card_infos.values())

    def is_absent_in_any(self, tag_name: str):
        """Retorna True se a tag estiver ausente em pelo menos uma das imagens carregadas."""
        return any(tag_name not in card.exif_data for card in self.card_infos.values())

    def apply_global_source_dest(self, source_key: str, dest_key: str, visible_tags: list = None):
        """
        Aplica globalmente uma regra 'Copiar de X Para Y'.
        Se dest_key for 'ALL', adiciona todas as chaves válidas exceto source_key.
        """
        target_tags = visible_tags if visible_tags is not None else self.all_tags
        for tag in target_tags:
            row = self.row_states[tag]
            if not source_key or source_key == "Nenhuma":
                row.source = ""
                row.destinations.clear()
            else:
                # Verifica se a origem realmente possui essa tag
                if tag in self.card_infos[source_key].exif_data:
                    row.source = source_key
                    if dest_key == "ALL":
                        row.destinations = {k for k in self.keys if k != source_key}
                    elif dest_key in self.keys and dest_key != source_key:
                        row.destinations = {dest_key}
                    else:
                        row.destinations.discard(source_key)
                else:
                    # Origem não possui a tag: mantém sem origem
                    row.source = ""
                    row.destinations.clear()

    def set_all_selected(self, selected: bool, visible_tags: list = None):
        """Marca ou desmarca a seleção para tags visíveis."""
        target_tags = visible_tags if visible_tags is not None else self.all_tags
        for tag in target_tags:
            row = self.row_states[tag]
            row.selected = selected
            if not selected:
                row.destinations.clear()
            elif row.source:
                row.destinations = {k for k in self.keys if k != row.source}

    def clear_all(self):
        """Remove todas as seleções, origens e destinos."""
        for row in self.row_states.values():
            row.selected = False
            row.source = ""
            row.destinations.clear()

    def compute_summary(self):
        """
        Calcula as estatísticas para o Resumo da Operação em tempo real:
        - total_selected: tags com selected == True
        - total_transfers: soma de destinos válidos em tags selecionadas com source válida
        - overwrites_count: transferências onde o valor de destino já existe e é diferente do valor de origem
        - incomplete_count: selecionadas mas sem source ou sem destino
        """
        total_selected = 0
        total_transfers = 0
        overwrites_count = 0
        incomplete_count = 0

        for tag, row in self.row_states.items():
            if row.selected:
                total_selected += 1
                if not row.source or not row.destinations:
                    incomplete_count += 1
                    continue
                # Se tem source válida
                src_card = self.card_infos.get(row.source)
                if not src_card or tag not in src_card.exif_data:
                    incomplete_count += 1
                    continue

                src_val = format_exif_value(src_card.exif_data[tag])
                for dest_key in row.destinations:
                    if dest_key == row.source:
                        continue
                    total_transfers += 1
                    dest_card = self.card_infos.get(dest_key)
                    if dest_card and tag in dest_card.exif_data:
                        dest_val = format_exif_value(dest_card.exif_data[tag])
                        if dest_val != src_val:
                            overwrites_count += 1

        return {
            "selected_count": total_selected,
            "transfers_count": total_transfers,
            "overwrites_count": overwrites_count,
            "incomplete_count": incomplete_count,
        }

