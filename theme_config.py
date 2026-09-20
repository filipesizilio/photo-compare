"""
================================================================================
Módulo: theme_config.py
Descrição: Carregamento de temas, gerenciamento de paleta de cores e estilos.
================================================================================
"""

import json
import os
import shutil
from app_paths import resource_path, get_app_data_dir, get_config_path


def _read_config():
    """Lê o arquivo config.json ou retorna dicionário vazio em caso de ausência/erro."""
    cfg_file = get_config_path()
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _write_config(data):
    """Grava as configurações no arquivo config.json preservando formatação."""
    cfg_file = get_config_path()
    try:
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Erro ao salvar configurações em config.json: {e}")


def get_user_themes_dir():
    """Retorna o diretório de temas do usuário em %APPDATA%/PhotoCompare/themes."""
    themes_dir = os.path.join(get_app_data_dir(), "themes")
    os.makedirs(themes_dir, exist_ok=True)
    return themes_dir


def ensure_user_themes():
    """Garante que a pasta %APPDATA%/PhotoCompare/themes e o tema inicial existam."""
    try:
        user_dir = get_user_themes_dir()
        dest_default = os.path.join(user_dir, "default.json")
        bundled_default = resource_path(os.path.join("themes", "default.json"))

        # Se default.json ainda não existir no APPDATA e existir o embutido, copia como ponto de partida
        if not os.path.exists(dest_default) and os.path.exists(bundled_default):
            shutil.copy2(bundled_default, dest_default)
        elif os.path.exists(dest_default) and os.path.exists(bundled_default):
            try:
                with open(dest_default, "r", encoding="utf-8") as f:
                    u_data = json.load(f)
                u_colors = u_data.get("colors", {})
                if "overlay_bg" not in u_colors or "overlay_alpha" not in u_data:
                    shutil.copy2(bundled_default, dest_default)
            except Exception:
                pass

        dest_readme = os.path.join(user_dir, "LEIAME.txt")
        bundled_readme = resource_path(os.path.join("themes", "LEIAME.txt"))
        if not os.path.exists(dest_readme) and os.path.exists(bundled_readme):
            shutil.copy2(bundled_readme, dest_readme)
        elif not os.path.exists(dest_readme):
            with open(dest_readme, "w", encoding="utf-8") as f:
                f.write(
                    "PASTA DE TEMAS DO PHOTOCOMPARE\n"
                    "==============================\n\n"
                    "Você pode editar o arquivo 'default.json' ou criar novos arquivos .json nesta pasta.\n\n"
                    "Para ativar um tema específico, altere no arquivo config.json (na pasta anterior):\n"
                    '{\n  "theme": "nome_do_arquivo_sem_extensao"\n}\n'
                )

        # Garante que config.json tenha a chave "theme" visível para o usuário
        config_data = _read_config()
        if "theme" not in config_data:
            config_data["theme"] = "default"
            _write_config(config_data)
    except Exception as e:
        print(f"Aviso ao inicializar pasta de temas do usuário: {e}")


def get_saved_theme_name():
    """Retorna o nome do tema salvo no config.json do usuário ou 'default'."""
    return _read_config().get("theme", "default")


def save_theme_name(theme_name):
    """Salva o nome do tema no config.json do usuário preservando outras configurações."""
    data = _read_config()
    data["theme"] = theme_name
    _write_config(data)


def get_saved_appearance_mode():
    """Retorna o modo de aparência salvo em config.json ('light', 'dark', 'system') ou None se não definido."""
    mode = _read_config().get("appearance_mode")
    return mode.lower() if mode and str(mode).lower() in ("light", "dark", "system") else None


def save_appearance_mode(mode):
    """Salva o modo de aparência no config.json do usuário preservando outras configurações."""
    data = _read_config()
    data["appearance_mode"] = str(mode).lower()
    _write_config(data)


def list_available_themes():
    """Lista os nomes de todos os temas disponíveis em APPDATA e nos embutidos."""
    themes = set()
    user_dir = get_user_themes_dir()
    if os.path.exists(user_dir):
        for f in os.listdir(user_dir):
            if f.lower().endswith(".json"):
                themes.add(os.path.splitext(f)[0])

    bundled_dir = resource_path("themes")
    if os.path.exists(bundled_dir):
        for f in os.listdir(bundled_dir):
            if f.lower().endswith(".json"):
                themes.add(os.path.splitext(f)[0])

    if not themes:
        themes.add("default")
    return sorted(list(themes))


def find_theme_file(theme_name):
    """Localiza o arquivo JSON de um tema, priorizando %APPDATA%/PhotoCompare/themes."""
    ensure_user_themes()
    if not theme_name:
        theme_name = get_saved_theme_name()
    user_file = os.path.join(get_user_themes_dir(), f"{theme_name}.json")
    if os.path.exists(user_file):
        return user_file

    bundled_file = resource_path(os.path.join("themes", f"{theme_name}.json"))
    if os.path.exists(bundled_file):
        return bundled_file

    default_user = os.path.join(get_user_themes_dir(), "default.json")
    if os.path.exists(default_user):
        return default_user

    default_bundled = resource_path(os.path.join("themes", "default.json"))
    if os.path.exists(default_bundled):
        return default_bundled

    return None


def load_theme(theme_name="default"):
    """
    Carrega o tema a partir do arquivo JSON especificado.
    Retorna um dicionário completo com garantia de fallback para todas as chaves.
    """
    if not theme_name:
        theme_name = get_saved_theme_name()
    theme_file = find_theme_file(theme_name)
    data = {}
    if theme_file and os.path.exists(theme_file):
        try:
            with open(theme_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar tema {theme_file}: {e}")
            data = {}

    # Se falhou e o tema solicitado não era o default, tenta carregar o default embutido como fallback
    if not data and theme_name != "default":
        fallback_file = resource_path(os.path.join("themes", "default.json"))
        if os.path.exists(fallback_file):
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}

    colors = data.get("colors", {})

    def _val(val, fallback):
        if val is None:
            return fallback
        if isinstance(val, list):
            return tuple(val)
        return val

    theme_config = {
        "appearance_mode": data.get("appearance_mode", "system"),
        "color_theme": data.get("color_theme", "blue"),
        "corner_radius": data.get("corner_radius", 6),
        "overlay_alpha": float(data.get("overlay_alpha", 0.55)),
        "colors": {
            "window_bg": _val(colors.get("window_bg"), ("#f4f4f5", "#0f0f11")),
            "toolbar_bg": _val(colors.get("toolbar_bg"), ("gray92", "#18181b")),
            "statusbar_bg": _val(colors.get("statusbar_bg"), ("gray92", "#18181b")),
            "columns_container_bg": _val(colors.get("columns_container_bg"), ("gray85", "#09090b")),
            "separator": _val(colors.get("separator"), ("gray80", "#27272a")),
            "brand_text": _val(colors.get("brand_text"), ("#18181b", "#f4f4f5")),
            "text_main": _val(colors.get("text_main"), ("#18181b", "#f4f4f5")),
            "text_muted": _val(colors.get("text_muted"), ("gray40", "#a1a1aa")),
            "link_text": _val(colors.get("link_text"), ("#2563eb", "#60a5fa")),
            "link_hover": _val(colors.get("link_hover"), ("#1d4ed8", "#93c5fd")),
            "primary": _val(colors.get("primary"), "#2563eb"),
            "primary_hover": _val(colors.get("primary_hover"), "#1d4ed8"),
            "primary_text": _val(colors.get("primary_text"), "white"),
            "transparent": _val(colors.get("transparent"), "transparent"),
            "hover_muted": _val(colors.get("hover_muted"), ("gray80", "#3f3f46")),
            "btn_action_fg": _val(colors.get("btn_action_fg"), ("gray75", "#3f3f46")),
            "btn_action_hover": _val(colors.get("btn_action_hover"), ("gray65", "#52525b")),
            "btn_action_text": _val(colors.get("btn_action_text"), ("#18181b", "#f4f4f5")),
            "btn_danger_fg": _val(colors.get("btn_danger_fg"), "#7f1d1d"),
            "btn_danger_hover": _val(colors.get("btn_danger_hover"), "#991b1b"),
            "btn_danger_text": _val(colors.get("btn_danger_text"), "white"),
            "sync_locked_fg": _val(colors.get("sync_locked_fg"), "#16a34a"),
            "sync_locked_hover": _val(colors.get("sync_locked_hover"), "#15803d"),
            "sync_unlocked_fg": _val(colors.get("sync_unlocked_fg"), "#4b5563"),
            "sync_unlocked_hover": _val(colors.get("sync_unlocked_hover"), "#374151"),
            "viewer_bg": _val(colors.get("viewer_bg"), ("gray90", "#18181b")),
            "viewer_header": _val(colors.get("viewer_header"), ("gray85", "#27272a")),
            "viewer_title": _val(colors.get("viewer_title"), ("#2563eb", "#60a5fa")),
            "canvas_bg": _val(colors.get("canvas_bg"), ("#f4f4f5", "#18181b")),
            "canvas_border": _val(colors.get("canvas_border"), ("#d4d4d8", "#27272a")),
            "empty_state_border": _val(colors.get("empty_state_border"), ("#a1a1aa", "#3f3f46")),
            "empty_state_text": _val(colors.get("empty_state_text"), ("#3f3f46", "#a1a1aa")),
            "empty_state_subtext": _val(colors.get("empty_state_subtext"), ("#71717a", "#71717a")),
            "border_image_a": _val(colors.get("border_image_a"), ("#2563eb", "#3b82f6")),
            "border_image_b": _val(colors.get("border_image_b"), ("#7c3aed", "#a855f7")),
            "border_image_c": _val(colors.get("border_image_c"), ("#0891b2", "#22d3ee")),
            "overlay_bg": _val(colors.get("overlay_bg"), ("#000000", "#000000")),
            "overlay_text": _val(colors.get("overlay_text"), ("#ffffff", "#ffffff")),
            "overlay_subtext": _val(colors.get("overlay_subtext"), ("#ebebeb", "#ebebeb")),
        }
    }
    return theme_config


def get_initial_appearance_mode():
    """Retorna o modo salvo em config.json se existir; senão retorna o padrão do tema."""
    saved = get_saved_appearance_mode()
    return saved if saved else CURRENT_THEME.get("appearance_mode", "system")


def get_mode_color(color_spec):
    """Retorna a cor correspondente ao modo de aparência ativo (Light ou Dark)."""
    if isinstance(color_spec, (tuple, list)):
        try:
            import customtkinter as ctk
            mode = ctk.get_appearance_mode()
            if mode not in ("Dark", "Light"):
                init_m = get_initial_appearance_mode()
                return color_spec[1] if init_m == "dark" else color_spec[0]
            return color_spec[1] if mode == "Dark" else color_spec[0]
        except Exception:
            return color_spec[0]
    return color_spec


# Carrega o tema padrão do arquivo JSON
CURRENT_THEME = load_theme("default")

# Exporta constantes: appearance_mode salvo em config.json tem precedência sobre o tema
DEFAULT_APPEARANCE_MODE = get_initial_appearance_mode()
DEFAULT_COLOR_THEME = CURRENT_THEME["color_theme"]
CORNER_RADIUS = CURRENT_THEME["corner_radius"]
OVERLAY_ALPHA = CURRENT_THEME.get("overlay_alpha", 0.55)

_colors = CURRENT_THEME["colors"]

COLOR_WINDOW_BG = _colors["window_bg"]
COLOR_TOOLBAR_BG = _colors["toolbar_bg"]
COLOR_STATUSBAR_BG = _colors["statusbar_bg"]
COLOR_COLUMNS_CONTAINER_BG = _colors["columns_container_bg"]
COLOR_SEPARATOR = _colors["separator"]

COLOR_BRAND_TEXT = _colors["brand_text"]
COLOR_TEXT_MAIN = _colors["text_main"]
COLOR_TEXT_MUTED = _colors["text_muted"]
COLOR_LINK_TEXT = _colors["link_text"]
COLOR_LINK_HOVER = _colors["link_hover"]

COLOR_PRIMARY = _colors["primary"]
COLOR_PRIMARY_HOVER = _colors["primary_hover"]
COLOR_PRIMARY_TEXT = _colors["primary_text"]

COLOR_TRANSPARENT = _colors["transparent"]
COLOR_HOVER_MUTED = _colors["hover_muted"]

COLOR_BTN_ACTION_FG = _colors["btn_action_fg"]
COLOR_BTN_ACTION_HOVER = _colors["btn_action_hover"]
COLOR_BTN_ACTION_TEXT = _colors["btn_action_text"]

COLOR_BTN_DANGER_FG = _colors["btn_danger_fg"]
COLOR_BTN_DANGER_HOVER = _colors["btn_danger_hover"]
COLOR_BTN_DANGER_TEXT = _colors["btn_danger_text"]

COLOR_SYNC_LOCKED_FG = _colors["sync_locked_fg"]
COLOR_SYNC_LOCKED_HOVER = _colors["sync_locked_hover"]
COLOR_SYNC_UNLOCKED_FG = _colors["sync_unlocked_fg"]
COLOR_SYNC_UNLOCKED_HOVER = _colors["sync_unlocked_hover"]

COLOR_VIEWER_BG = _colors["viewer_bg"]
COLOR_VIEWER_HEADER = _colors["viewer_header"]
COLOR_VIEWER_TITLE = _colors["viewer_title"]
COLOR_CANVAS_BG = _colors["canvas_bg"]
COLOR_CANVAS_BORDER = _colors["canvas_border"]
COLOR_EMPTY_STATE_BORDER = _colors["empty_state_border"]
COLOR_EMPTY_STATE_TEXT = _colors["empty_state_text"]
COLOR_EMPTY_STATE_SUBTEXT = _colors["empty_state_subtext"]

COLOR_BORDER_IMAGE_A = _colors["border_image_a"]
COLOR_BORDER_IMAGE_B = _colors["border_image_b"]
COLOR_BORDER_IMAGE_C = _colors["border_image_c"]

COLOR_OVERLAY_BG = _colors["overlay_bg"]
COLOR_OVERLAY_TEXT = _colors["overlay_text"]
COLOR_OVERLAY_SUBTEXT = _colors["overlay_subtext"]


def get_accent_color_for_title(title):
    """Retorna a cor de destaque da borda associada à imagem (Imagem A = Azul, B = Violeta, C = Ciano/Turquesa)."""
    t = str(title).upper().strip()
    words = t.replace(":", " ").replace("-", " ").split()
    if "B" in words or t.endswith("B"):
        return COLOR_BORDER_IMAGE_B
    if "C" in words or t.endswith("C"):
        return COLOR_BORDER_IMAGE_C
    if "A" in words or t.endswith("A"):
        return COLOR_BORDER_IMAGE_A
    return COLOR_BORDER_IMAGE_A
