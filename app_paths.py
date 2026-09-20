"""
================================================================================
Módulo: app_paths.py
Descrição: Resolução de caminhos de arquivos, diretório APPDATA e configurações.
================================================================================
"""

import os
import sys


def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com execução normal e empacotada (.exe)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_app_data_dir():
    """Retorna o diretório base de dados/configurações do PhotoCompare no APPDATA do usuário."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = os.path.join(appdata, "PhotoCompare")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def get_config_path():
    """Retorna o caminho para o arquivo de configuração JSON de preferências da janela."""
    return os.path.join(get_app_data_dir(), "config.json")

