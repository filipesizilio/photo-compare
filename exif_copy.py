"""
================================================================================
Módulo: exif_copy.py
Descrição: Processamento e execução segura de cópia e transferência seletiva
           de metadados EXIF entre múltiplas imagens utilizando Piexif.
================================================================================
"""

import os
import shutil
from PIL import Image, ExifTags


SUPPORTED_EXIF_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".webp"}


def check_file_exif_writable(file_path: str):
    """
    Verifica se o formato do arquivo é suportado pelo Piexif para gravação direta de EXIF.
    Retorna (is_writable: bool, reason: str).
    """
    if not file_path or not os.path.exists(file_path):
        return False, "Arquivo não encontrado."

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXIF_EXTENSIONS:
        if ext == ".png":
            return False, "O formato PNG possui suporte restrito a metadados nativos EXIF via Piexif. Apenas JPG/TIFF/WEBP são suportados para gravação completa."
        return False, f"Formato '{ext}' não suportado para gravação direta de metadados EXIF."

    # Verifica permissão de escrita
    if not os.access(file_path, os.W_OK):
        return False, "Sem permissão de escrita no arquivo."

    return True, ""


def execute_planned_exif_transfers(compare_state, progress_callback=None):
    """
    Executa o plano de transferência configurado no compare_state.
    
    Args:
        compare_state (ExifCompareState): Estado configurado na tabela.
        progress_callback: Função opcional progress_callback(current, total, status_message)

    Returns:
        dict: {
            "success": bool,
            "transferred_count": int,
            "modified_destinations": list of str (nomes dos arquivos alterados),
            "errors": list of str,
            "warnings": list of str
        }
    """
    import piexif

    # 1. Monta o mapa de operações agrupado por destino:
    # { dest_key: { (ifd_name, tag_id): (source_key, raw_value, tag_name) } }
    dest_operations = {k: {} for k in compare_state.keys}
    total_ops = 0

    # Carrega os raw EXIF dicts de todas as imagens de origem necessárias
    loaded_raw_exif = {}  # { key: piexif_dict }
    for key, card in compare_state.card_infos.items():
        if card.file_path and os.path.exists(card.file_path):
            try:
                with Image.open(card.file_path) as img:
                    exif_bytes = img.info.get('exif')
                    if exif_bytes:
                        loaded_raw_exif[key] = piexif.load(exif_bytes)
                    else:
                        loaded_raw_exif[key] = {
                            "0th": {}, "Exif": {}, "GPS": {},
                            "Interop": {}, "1st": {}, "thumbnail": None,
                        }
            except Exception as e:
                loaded_raw_exif[key] = {
                    "0th": {}, "Exif": {}, "GPS": {},
                    "Interop": {}, "1st": {}, "thumbnail": None,
                }

    # Prepara o catálogo de mapeamento tag_name -> (ifd_name, tag_id) por chave
    tag_catalog = {}  # { key: { tag_name: (ifd_name, tag_id, value) } }
    for key, exif_dict in loaded_raw_exif.items():
        tag_catalog[key] = {}
        for ifd_name in ["0th", "Exif", "GPS", "Interop", "1st"]:
            for tag_id, val in exif_dict.get(ifd_name, {}).items():
                tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                tag_catalog[key][tag_name] = (ifd_name, tag_id, val)

    # Identifica as transferências selecionadas
    for tag_name, row in compare_state.row_states.items():
        if not row.selected or not row.source or not row.destinations:
            continue
        src_key = row.source
        if src_key not in tag_catalog or tag_name not in tag_catalog[src_key]:
            continue

        ifd_name, tag_id, raw_val = tag_catalog[src_key][tag_name]
        for dest_key in row.destinations:
            if dest_key == src_key:
                continue
            dest_operations[dest_key][(ifd_name, tag_id)] = (src_key, raw_val, tag_name)
            total_ops += 1

    if total_ops == 0:
        return {
            "success": False,
            "transferred_count": 0,
            "modified_destinations": [],
            "errors": ["Nenhuma transferência válida selecionada."],
            "warnings": []
        }

    # 2. Valida compatibilidade de todos os arquivos de destino que receberão alterações
    errors = []
    warnings = []
    destinations_to_modify = [k for k, ops in dest_operations.items() if ops]

    for dest_key in destinations_to_modify:
        card = compare_state.card_infos[dest_key]
        writable, reason = check_file_exif_writable(card.file_path)
        if not writable:
            errors.append(f"Imagem {dest_key} ({card.file_name}): {reason}")

    if errors:
        return {
            "success": False,
            "transferred_count": 0,
            "modified_destinations": [],
            "errors": errors,
            "warnings": warnings
        }

    # 3. Executa a aplicação das tags e gravação dos arquivos com backup de segurança
    modified_files = []
    completed_ops = 0

    for dest_key in destinations_to_modify:
        card = compare_state.card_infos[dest_key]
        dest_path = card.file_path
        ops_dict = dest_operations[dest_key]

        if progress_callback:
            progress_callback(completed_ops, total_ops, f"Atualizando Imagem {dest_key} ({card.file_name})...")

        # Cria backup temporário antes de gravar
        backup_path = dest_path + ".pc_backup"
        try:
            shutil.copy2(dest_path, backup_path)
        except Exception as e:
            errors.append(f"Não foi possível criar cópia de segurança para {card.file_name}: {e}")
            continue

        try:
            with Image.open(dest_path) as img:
                exif_bytes = img.info.get('exif')
                if exif_bytes:
                    to_exif_dict = piexif.load(exif_bytes)
                else:
                    to_exif_dict = {
                        "0th": {}, "Exif": {}, "GPS": {},
                        "Interop": {}, "1st": {}, "thumbnail": None,
                    }

                # Aplica as tags transferidas
                for (ifd_name, tag_id), (src_key, raw_val, tag_name) in ops_dict.items():
                    if ifd_name not in to_exif_dict:
                        to_exif_dict[ifd_name] = {}
                    to_exif_dict[ifd_name][tag_id] = raw_val
                    completed_ops += 1

                new_exif_bytes = piexif.dump(to_exif_dict)
                img.save(dest_path, exif=new_exif_bytes)

            # Gravação bem-sucedida: remove o backup temporário
            if os.path.exists(backup_path):
                os.remove(backup_path)

            modified_files.append(card.file_name)

            # Atualiza os dados carregados em memória no card do viewer
            card._load_details()

        except Exception as e:
            # Em caso de falha, restaura o backup imediatamente
            if os.path.exists(backup_path):
                try:
                    shutil.copy2(backup_path, dest_path)
                    os.remove(backup_path)
                except Exception:
                    pass
            errors.append(f"Falha ao salvar EXIF em {card.file_name}: {e}")

    if progress_callback:
        progress_callback(total_ops, total_ops, "Operação concluída.")

    return {
        "success": len(modified_files) > 0 and len(errors) == 0,
        "transferred_count": completed_ops,
        "modified_destinations": modified_files,
        "errors": errors,
        "warnings": warnings
    }
