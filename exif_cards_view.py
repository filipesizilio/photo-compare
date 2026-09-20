"""
================================================================================
Módulo: exif_cards_view.py
Descrição: Renderização dos cards superiores com miniaturas e metadados das imagens.
================================================================================
"""

import tkinter as tk
import customtkinter as ctk
from PIL import ImageTk

from app_config import (
    CORNER_RADIUS,
    COLOR_VIEWER_BG,
    COLOR_VIEWER_HEADER,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    COLOR_BORDER_IMAGE_A,
    get_mode_color,
)
from ui_tooltip import add_tooltip


def build_image_cards(parent, keys, card_infos, border_colors, photo_images_ref):
    """
    Constrói a seção horizontal de cards para cada imagem comparada.

    Args:
        parent: Widget contêiner onde os cards serão inseridos.
        keys: Lista de identificadores das imagens ('A', 'B', ['C']).
        card_infos: Dicionário mapeando chave para ImageCardInfo.
        border_colors: Dicionário mapeando chave para cor de destaque.
        photo_images_ref: Lista para reter referências PhotoImage contra garbage collection.

    Returns:
        ctk.CTkFrame: Frame contendo os cards construídos.
    """
    cards_frame = ctk.CTkFrame(parent, fg_color="transparent")
    cards_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

    for idx, key in enumerate(keys):
        cards_frame.columnconfigure(idx, weight=1, uniform="img_cards")
        card = card_infos[key]
        accent_color = border_colors.get(key, COLOR_BORDER_IMAGE_A)

        card_widget = ctk.CTkFrame(
            cards_frame,
            fg_color=COLOR_VIEWER_BG,
            corner_radius=CORNER_RADIUS,
            border_width=3,
            border_color=accent_color,
            height=95,
        )
        card_widget.grid(row=0, column=idx, sticky="nsew", padx=4, pady=2)
        card_widget.pack_propagate(False)

        # Layout horizontal interno: [Miniatura] + [Detalhes textuais]
        inner_container = tk.Frame(card_widget, bg=get_mode_color(COLOR_VIEWER_BG))
        inner_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # Miniatura ou Placeholder
        thumb_label = tk.Label(
            inner_container,
            bg=get_mode_color(COLOR_VIEWER_HEADER),
            width=100,
            height=70,
        )
        thumb_label.pack(side=tk.LEFT, padx=(0, 10))

        if card.thumbnail_image:
            try:
                tk_thumb = ImageTk.PhotoImage(card.thumbnail_image)
                photo_images_ref.append(tk_thumb)
                thumb_label.configure(
                    image=tk_thumb,
                    width=card.thumbnail_image.width,
                    height=card.thumbnail_image.height,
                )
            except Exception:
                thumb_label.configure(text="🖼️", fg="#71717a", font=("Segoe UI", 16))
        else:
            thumb_label.configure(text="🖼️\nSem prévia", fg="#71717a", font=("Segoe UI", 9))

        # Detalhes textuais
        info_col = tk.Frame(inner_container, bg=get_mode_color(COLOR_VIEWER_BG))
        info_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header_title = tk.Label(
            info_col,
            text=f"{card.title}",
            font=("Segoe UI", 11, "bold"),
            fg=get_mode_color(accent_color),
            bg=get_mode_color(COLOR_VIEWER_BG),
            anchor="w",
        )
        header_title.pack(anchor="w")

        name_lbl = tk.Label(
            info_col,
            text=card.file_name,
            font=("Segoe UI", 9, "bold"),
            fg=get_mode_color(COLOR_TEXT_MAIN),
            bg=get_mode_color(COLOR_VIEWER_BG),
            anchor="w",
        )
        name_lbl.pack(anchor="w")
        add_tooltip(name_lbl, card.file_path)

        res_str = f"{card.orig_size[0]} x {card.orig_size[1]}" if card.orig_size != (0, 0) else "—"
        exif_status = "✓ EXIF presente" if card.has_exif else "⚠ Sem dados EXIF"

        meta_lbl = tk.Label(
            info_col,
            text=f"Resolução: {res_str}  •  Data: {card.file_date_str}\nStatus: {exif_status}",
            font=("Segoe UI", 8),
            fg=get_mode_color(COLOR_TEXT_MUTED),
            bg=get_mode_color(COLOR_VIEWER_BG),
            justify=tk.LEFT,
            anchor="w",
        )
        meta_lbl.pack(anchor="w")

    return cards_frame

