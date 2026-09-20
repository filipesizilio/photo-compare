"""
================================================================================
Módulo: app_config.py
Descrição: Gerenciamento de configuração da aplicação (geometria, caminho de
           configuração, estado da janela, ícone).
================================================================================
"""

import json
import os
import tkinter as tk

from app_paths import (
    resource_path,
    get_app_data_dir,
    get_config_path,
)

from theme_config import (
    get_user_themes_dir,
    ensure_user_themes,
    get_saved_theme_name,
    save_theme_name,
    get_saved_appearance_mode,
    save_appearance_mode,
    get_initial_appearance_mode,
    list_available_themes,
    find_theme_file,
    load_theme,
    get_mode_color,
    get_accent_color_for_title,
    CURRENT_THEME,
    DEFAULT_APPEARANCE_MODE,
    DEFAULT_COLOR_THEME,
    CORNER_RADIUS,
    OVERLAY_ALPHA,
    COLOR_WINDOW_BG,
    COLOR_TOOLBAR_BG,
    COLOR_STATUSBAR_BG,
    COLOR_COLUMNS_CONTAINER_BG,
    COLOR_SEPARATOR,
    COLOR_BRAND_TEXT,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    COLOR_LINK_TEXT,
    COLOR_LINK_HOVER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_TEXT,
    COLOR_TRANSPARENT,
    COLOR_HOVER_MUTED,
    COLOR_BTN_ACTION_FG,
    COLOR_BTN_ACTION_HOVER,
    COLOR_BTN_ACTION_TEXT,
    COLOR_BTN_DANGER_FG,
    COLOR_BTN_DANGER_HOVER,
    COLOR_BTN_DANGER_TEXT,
    COLOR_SYNC_LOCKED_FG,
    COLOR_SYNC_LOCKED_HOVER,
    COLOR_SYNC_UNLOCKED_FG,
    COLOR_SYNC_UNLOCKED_HOVER,
    COLOR_VIEWER_BG,
    COLOR_VIEWER_HEADER,
    COLOR_VIEWER_TITLE,
    COLOR_CANVAS_BG,
    COLOR_CANVAS_BORDER,
    COLOR_EMPTY_STATE_BORDER,
    COLOR_EMPTY_STATE_TEXT,
    COLOR_EMPTY_STATE_SUBTEXT,
    COLOR_BORDER_IMAGE_A,
    COLOR_BORDER_IMAGE_B,
    COLOR_BORDER_IMAGE_C,
    COLOR_OVERLAY_BG,
    COLOR_OVERLAY_TEXT,
    COLOR_OVERLAY_SUBTEXT,
)


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
        """Salva a geometria e o estado maximizado da janela antes de fechar preservando outras configurações."""
        try:
            is_maximized = (self.root.state() == "zoomed")
            geom = self._last_normal_geometry or self.root.geometry()
            config_data = {}
            if os.path.exists(self._config_path):
                try:
                    with open(self._config_path, "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                except Exception:
                    config_data = {}
            config_data["maximized"] = is_maximized
            config_data["geometry"] = geom
            if "theme" not in config_data:
                config_data["theme"] = get_saved_theme_name()
            if "appearance_mode" not in config_data:
                saved_mode = get_saved_appearance_mode()
                if saved_mode:
                    config_data["appearance_mode"] = saved_mode
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


def get_exif_geometry():
    """Retorna a geometria salva para o popup EXIF ou None."""
    config_file = get_config_path()
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("exif_geometry")
        except Exception:
            pass
    return None


def save_exif_geometry(geom_str):
    """Salva a geometria do popup EXIF em config.json."""
    if not geom_str:
        return
    config_file = get_config_path()
    data = {}
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["exif_geometry"] = geom_str
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as err:
        print(f"Erro ao salvar geometria EXIF: {err}")