"""
================================================================================
Módulo: app_config.py
Descrição: Gerenciamento de configuração da aplicação (geometria, caminho de
           configuração, estado da janela, ícone).
================================================================================
"""

import json
import os
import sys
import tkinter as tk


def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com execução normal e empacotada (.exe)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def get_config_path():
    """Retorna o caminho para o arquivo de configuração JSON de preferências da janela."""
    appdata = os.environ.get("APPDATA")
    if appdata:
        base_dir = os.path.join(appdata, "PhotoCompare")
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "config.json")


class AppConfig:
    """Gerencia a configuração persistente da aplicação."""

    def __init__(self, root_window):
        self.root = root_window
        self._config_path = get_config_path()
        self._last_normal_geometry = None

    def load_and_apply_geometry(self):
        """Restaura a geometria e o estado da janela salvo ou inicia maximizado por padrão."""
        config = {}
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                config = {}

        # Aplica geometria da sessão anterior se existir
        geom = config.get("geometry", "1280x760")
        try:
            self.root.geometry(geom)
            self._last_normal_geometry = geom
        except Exception:
            self.root.geometry("1280x760")

        # Abre maximizado por padrão (ou restaura estado maximizado salvo)
        should_maximize = config.get("maximized", True)
        if should_maximize:
            try:
                self.root.state("zoomed")
            except Exception:
                pass

    def on_window_configure(self, event):
        """Registra a geometria normal sempre que a janela não estiver maximizada."""
        if event.widget == self.root:
            try:
                if self.root.state() != "zoomed":
                    self._last_normal_geometry = self.root.geometry()
            except Exception:
                pass

    def on_close(self):
        """Salva a geometria e o estado maximizado da janela antes de fechar."""
        try:
            is_maximized = (self.root.state() == "zoomed")
            geom = self._last_normal_geometry or self.root.geometry()
            config_data = {
                "maximized": is_maximized,
                "geometry": geom
            }
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)
        except Exception as err:
            print(f"Erro ao salvar configurações de janela: {err}")

    def set_app_icon(self):
        """Define o ícone da aplicação na barra de título e barra de tarefas."""
        icon_ico = resource_path(os.path.join("assets", "icon.ico"))
        icon_png = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_ico):
            try:
                self.root.iconbitmap(icon_ico)
            except Exception:
                pass
        if os.path.exists(icon_png):
            try:
                self.root._app_icon_img = tk.PhotoImage(file=icon_png)
                self.root.iconphoto(True, self.root._app_icon_img)
            except Exception:
                pass