import os
import tkinter as tk
import customtkinter as ctk

from app_config import (
    CORNER_RADIUS,
    COLOR_WINDOW_BG,
    COLOR_TOOLBAR_BG,
    COLOR_BRAND_TEXT,
    COLOR_BTN_DANGER_FG,
    COLOR_BTN_DANGER_HOVER,
    COLOR_BTN_DANGER_TEXT,
)


def create_exif_popup(parent, column_count):
    """Cria a janela, cabeçalho e botão de fechamento do popup EXIF."""
    popup = ctk.CTkToplevel(parent)
    popup.title("Comparação de Dados EXIF")
    popup.geometry("1400x800")
    popup.minsize(1000, 600)
    popup.configure(fg_color=COLOR_WINDOW_BG)

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
    except Exception:
        pass

    for column in range(column_count):
        popup.columnconfigure(column, weight=1, uniform="exif_cols")
    popup.rowconfigure(1, weight=1)

    header = ctk.CTkFrame(
        popup,
        fg_color=COLOR_TOOLBAR_BG,
        corner_radius=0,
        height=50
    )
    header.grid(row=0, column=0, columnspan=column_count, sticky="ew", padx=4, pady=4)
    header.pack_propagate(False)

    ctk.CTkLabel(
        header,
        text="Comparação de Metadados EXIF",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=COLOR_BRAND_TEXT
    ).pack(side=tk.LEFT, padx=12, pady=10)

    ctk.CTkButton(
        header,
        text="✕ Fechar",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=COLOR_BTN_DANGER_FG,
        hover_color=COLOR_BTN_DANGER_HOVER,
        text_color=COLOR_BTN_DANGER_TEXT,
        width=80,
        height=32,
        corner_radius=CORNER_RADIUS,
        command=popup.destroy,
    ).pack(side=tk.RIGHT, padx=12, pady=8)

    return popup
