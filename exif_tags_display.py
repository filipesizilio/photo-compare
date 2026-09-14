"""
================================================================================
Módulo: exif_tags_display.py
Descrição: Funções para exibição estruturada de dados EXIF com checkboxes.
================================================================================
"""

import tkinter as tk
from tkinter import ttk


def create_exif_display(scrollable_frame, exif_data, on_selection_change=None):
    """
    Cria a exibição estruturada de dados EXIF com checkboxes.
    
    Args:
        scrollable_frame: Frame onde os widgets serão criados
        exif_data: Dicionário com dados EXIF
        on_selection_change: Callback opcional quando seleção muda
        
    Returns:
        tuple: (tag_vars, tag_checkboxes, btn_select_all, btn_deselect_all)
    """
    # Armazena checkboxes e variáveis para cada tag
    tag_checkboxes = {}
    tag_vars = {}
    
    # Frame para botão "Selecionar Tudo"
    select_all_frame = tk.Frame(scrollable_frame, bg="#09090b")
    select_all_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
    
    btn_select_all = tk.Button(
        select_all_frame,
        text="☑ Selecionar Tudo",
        font=("Segoe UI", 8, "bold"),
        bg="#3f3f46",
        fg="#f4f4f5",
        activebackground="#52525b",
        activeforeground="white",
        relief=tk.FLAT,
        padx=8,
        pady=2,
        cursor="hand2",
        state=tk.DISABLED
    )
    btn_select_all.pack(side=tk.LEFT, padx=(0, 8))
    
    btn_deselect_all = tk.Button(
        select_all_frame,
        text="☐ Desmarcar Tudo",
        font=("Segoe UI", 8),
        bg="#3f3f46",
        fg="#f4f4f5",
        activebackground="#52525b",
        activeforeground="white",
        relief=tk.FLAT,
        padx=8,
        pady=2,
        cursor="hand2",
        state=tk.DISABLED
    )
    btn_deselect_all.pack(side=tk.LEFT)
    
    # Agrupa por categoria
    categories = {
        "Imagem": ["ImageWidth", "ImageLength", "BitsPerSample", "Compression", "PhotometricInterpretation", "Orientation", "SamplesPerPixel", "PlanarConfiguration", "YCbCrSubSampling", "YCbCrPositioning", "XResolution", "YResolution", "ResolutionUnit"],
        "Câmera": ["Make", "Model", "Software", "DateTime", "Artist", "Copyright"],
        "Exposição": ["ExposureTime", "FNumber", "ExposureProgram", "SpectralSensitivity", "ISOSpeedRatings", "OECF", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "ExposureBiasValue", "MaxApertureValue", "SubjectDistance", "MeteringMode", "LightSource", "Flash", "FocalLength", "SubjectArea", "MakerNote", "UserComment", "SubsecTime", "SubsecTimeOriginal", "SubsecTimeDigitized"],
        "Data/Hora": ["DateTimeOriginal", "DateTimeDigitized", "OffsetTime", "OffsetTimeOriginal", "OffsetTimeDigitized"],
        "GPS": ["GPSVersionID", "GPSLatitudeRef", "GPSLatitude", "GPSLongitudeRef", "GPSLongitude", "GPSAltitudeRef", "GPSAltitude", "GPSTimeStamp", "GPSSatellites", "GPSStatus", "GPSMeasureMode", "GPSDOP", "GPSSpeedRef", "GPSSpeed", "GPSTrackRef", "GPSTrack", "GPSImgDirectionRef", "GPSImgDirection", "GPSMapDatum", "GPSDestLatitudeRef", "GPSDestLatitude", "GPSDestLongitudeRef", "GPSDestLongitude", "GPSDestBearingRef", "GPSDestBearing", "GPSDestDistanceRef", "GPSDestDistance", "GPSProcessingMethod", "GPSAreaInformation", "GPSDateStamp", "GPSDifferential"],
        "Outros": []
    }
    
    # Adiciona tags não categorizadas em "Outros"
    categorized_tags = set()
    for cat_tags in categories.values():
        categorized_tags.update(cat_tags)
    
    for tag in exif_data:
        if tag not in categorized_tags:
            categories["Outros"].append(tag)
    
    # Remove categorias vazias
    categories = {k: v for k, v in categories.items() if v}
    
    row = 1  # Começa na linha 1 (linha 0 é o botão Selecionar Tudo)
    for category, tags in categories.items():
        # Cabeçalho da categoria
        cat_label = tk.Label(
            scrollable_frame,
            text=category,
            font=("Segoe UI", 9, "bold"),
            fg="#a5b4fc",
            bg="#09090b",
            anchor="w"
        )
        cat_label.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 2))
        row += 1
        
        # Separador
        sep = tk.Frame(scrollable_frame, bg="#27272a", height=1)
        sep.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8)
        row += 1
        
        for tag in tags:
            if tag in exif_data:
                value = exif_data[tag]
                # Formata o valor para exibição
                if isinstance(value, bytes):
                    try:
                        value = value.decode('utf-8', errors='replace')
                    except:
                        value = str(value)
                elif isinstance(value, tuple):
                    value = str(value)
                
                # Limita o tamanho do valor exibido
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                
                # Checkbox para seleção
                var = tk.BooleanVar(value=False)
                tag_vars[tag] = var
                
                cb = tk.Checkbutton(
                    scrollable_frame,
                    variable=var,
                    font=("Segoe UI", 8),
                    fg="#e4e4e7",
                    bg="#09090b",
                    selectcolor="#18181b",
                    activebackground="#09090b",
                    activeforeground="#e4e4e7",
                    cursor="hand2",
                    state=tk.DISABLED
                )
                cb.grid(row=row, column=0, sticky="w", padx=(12, 4), pady=1)
                tag_checkboxes[tag] = cb
                
                # Label da tag
                tag_label = tk.Label(
                    scrollable_frame,
                    text=tag,
                    font=("Segoe UI", 8),
                    fg="#71717a",
                    bg="#09090b",
                    anchor="w",
                    justify="left"
                )
                tag_label.grid(row=row, column=1, sticky="nw", padx=(0, 4), pady=1)
                
                # Label do valor
                val_label = tk.Label(
                    scrollable_frame,
                    text=value_str,
                    font=("Segoe UI", 8),
                    fg="#e4e4e7",
                    bg="#09090b",
                    anchor="w",
                    justify="left",
                    wraplength=300
                )
                val_label.grid(row=row, column=2, sticky="nw", padx=(0, 12), pady=1)
                row += 1
    
    return tag_vars, tag_checkboxes, btn_select_all, btn_deselect_all


def create_no_exif_message(scrollable_frame):
    """
    Cria mensagem para imagens sem dados EXIF.
    
    Args:
        scrollable_frame: Frame onde a mensagem será exibida
    """
    tk.Label(
        scrollable_frame,
        text="Nenhum dado EXIF encontrado nesta imagem.\n\nEsta imagem pode receber dados EXIF de outra imagem\nselecionando 'Destino (To)'.",
        font=("Segoe UI", 9),
        fg="#71717a",
        bg="#09090b",
        justify=tk.CENTER
    ).grid(row=1, column=0, columnspan=3, padx=20, pady=40, sticky="nsew")
    # Configura a linha e coluna para expandir
    scrollable_frame.rowconfigure(1, weight=1)
    scrollable_frame.columnconfigure(0, weight=1)


def enable_selection_controls(tag_checkboxes, btn_select_all, btn_deselect_all, enabled=True):
    """
    Habilita ou desabilita controles de seleção.
    
    Args:
        tag_checkboxes: Dicionário de checkboxes
        btn_select_all: Botão "Selecionar Tudo"
        btn_deselect_all: Botão "Desmarcar Tudo"
        enabled: True para habilitar, False para desabilitar
    """
    state = tk.NORMAL if enabled else tk.DISABLED
    for cb in tag_checkboxes.values():
        cb.config(state=state)
    btn_select_all.config(state=state)
    btn_deselect_all.config(state=state)


def select_all_tags(tag_vars):
    """Seleciona todas as tags."""
    for var in tag_vars.values():
        var.set(True)


def deselect_all_tags(tag_vars):
    """Desmarca todas as tags."""
    for var in tag_vars.values():
        var.set(False)


def get_selected_tags(tag_vars):
    """Retorna lista de tags selecionadas."""
    return [tag for tag, var in tag_vars.items() if var.get()]