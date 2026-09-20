"""
================================================================================
Módulo: exif_popup_layout.py
Descrição: Estrutura base da janela, cabeçalho e componentes de layout para o
           popup unificado de metadados EXIF.
================================================================================
"""

import os
import tkinter as tk
import customtkinter as ctk

from app_config import (
    CORNER_RADIUS,
    COLOR_WINDOW_BG,
    COLOR_TOOLBAR_BG,
    COLOR_BRAND_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_BTN_DANGER_FG,
    COLOR_BTN_DANGER_HOVER,
    COLOR_BTN_DANGER_TEXT,
    get_exif_geometry,
    save_exif_geometry,
)


def create_exif_window(parent):
    """
    Cria a janela CTkToplevel com persistência de geometria e cabeçalho.
    """
    popup = ctk.CTkToplevel(parent)
    popup.title("Comparar e Copiar Metadados EXIF")
    popup.minsize(980, 620)
    popup.configure(fg_color=COLOR_WINDOW_BG)

    # Restaura geometria salva (tamanho e posição) ou usa dimensão padrão elegante centralizada
    saved_geom = get_exif_geometry()
    geometry_applied = False

    if saved_geom:
        try:
            parts = saved_geom.replace("+", "x").replace("-", "x").split("x")
            if len(parts) >= 2:
                tw = max(980, int(parts[0]))
                th = max(620, int(parts[1]))
                if len(parts) >= 4:
                    tx = int(parts[2])
                    ty = int(parts[3])
                    screen_w = popup.winfo_screenwidth()
                    screen_h = popup.winfo_screenheight()
                    if 0 <= tx < screen_w - 100 and 0 <= ty < screen_h - 100:
                        popup.geometry(f"{tw}x{th}+{tx}+{ty}")
                        geometry_applied = True
                if not geometry_applied:
                    parent.update_idletasks()
                    pw = parent.winfo_width()
                    ph = parent.winfo_height()
                    px = parent.winfo_x()
                    py = parent.winfo_y()
                    x = max(10, px + (pw // 2) - (tw // 2))
                    y = max(10, py + (ph // 2) - (th // 2))
                    popup.geometry(f"{tw}x{th}+{x}+{y}")
                    geometry_applied = True
        except Exception:
            pass

    if not geometry_applied:
        tw, th = 1280, 820
        try:
            parent.update_idletasks()
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_x()
            py = parent.winfo_y()
            x = max(10, px + (pw // 2) - (tw // 2))
            y = max(10, py + (ph // 2) - (th // 2))
            popup.geometry(f"{tw}x{th}+{x}+{y}")
        except Exception:
            popup.geometry(f"{tw}x{th}")

    # Ícone
    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
    except Exception:
        pass

    # Listener para salvar geometria ao fechar
    def _save_geom():
        try:
            if popup.state() != "zoomed":
                save_exif_geometry(popup.geometry())
        except Exception:
            pass

    popup.protocol("WM_DELETE_WINDOW", lambda: (_save_geom(), popup.destroy()))

    # Layout de linhas:
    # row 0: Cabeçalho (fixo)
    # row 1: Cards das imagens (fixo)
    # row 2: Barra de ações globais (fixo)
    # row 3: Tabela comparativa (expansível)
    # row 4: Resumo e ações finais (fixo)
    popup.columnconfigure(0, weight=1)
    popup.rowconfigure(3, weight=1)

    # 1. Cabeçalho
    header = ctk.CTkFrame(
        popup,
        fg_color=COLOR_TOOLBAR_BG,
        corner_radius=0,
        height=62
    )
    header.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 4))
    header.pack_propagate(False)

    title_container = ctk.CTkFrame(header, fg_color="transparent")
    title_container.pack(side=tk.LEFT, padx=16, pady=6)

    # Título com ícone embutido
    title_line = ctk.CTkFrame(title_container, fg_color="transparent")
    title_line.pack(anchor="w")

    ctk.CTkLabel(
        title_line,
        text="🏷️",
        font=ctk.CTkFont(size=18),
    ).pack(side=tk.LEFT, padx=(0, 8))

    ctk.CTkLabel(
        title_line,
        text="Comparar e Copiar Metadados EXIF",
        font=ctk.CTkFont(size=15, weight="bold"),
        text_color=COLOR_BRAND_TEXT
    ).pack(side=tk.LEFT)

    ctk.CTkLabel(
        title_container,
        text="Compare e transfira seletivamente os metadados entre imagens.",
        font=ctk.CTkFont(size=11),
        text_color=COLOR_TEXT_MUTED
    ).pack(anchor="w", padx=(28, 0))

    return popup
