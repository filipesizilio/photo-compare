
"""
================================================================================
Módulo: exif_tools.py
Descrição: Camada de compatibilidade que re-exporta funções dos módulos especializados.
           Mantém compatibilidade com código existente que importa de exif_tools.
================================================================================
"""

# Re-exporta funções do módulo GUI
from exif_gui import show_exif_comparison_popup

# Re-exporta funções do módulo core
from exif_core import (
    _get_exif_data,
    _transfer_exif_data,
    _clean_exif_data,
    copy_exif_tags_between_images,
)

# Re-exporta funções do módulo GPS
from exif_gps import (
    _gps_to_gmaps,
    _write_gps_to_exif,
)
