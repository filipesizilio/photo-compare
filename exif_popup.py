"""
================================================================================
Módulo: exif_popup.py
Descrição: Janela principal para comparação e cópia de metadados EXIF.
================================================================================
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from exif_models import ImageCardInfo, ExifCompareState
from exif_copy import execute_planned_exif_transfers
from exif_popup_layout import create_exif_window
from exif_cards_view import build_image_cards
from exif_actions_bar import ExifActionsBar
from exif_table_view import ExifTableView, BORDER_COLORS
from app_config import (
    CORNER_RADIUS,
    COLOR_TOOLBAR_BG,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_TEXT,
    COLOR_BTN_ACTION_FG,
    COLOR_BTN_ACTION_HOVER,
    COLOR_BTN_ACTION_TEXT,
    save_exif_geometry,
    get_mode_color,
)


def show_exif_comparison_popup(parent, viewers):
    """
    Abre o popup consolidado de comparação e cópia de metadados EXIF.

    Args:
        parent: Janela principal do PhotoCompare.
        viewers: Lista com os visualizadores ativos (2 ou 3).
    """
    valid_viewers = [v for v in viewers if getattr(v, "pil_image", None) and getattr(v, "file_path", None)]

    if not valid_viewers:
        messagebox.showinfo("Sem imagens", "Nenhuma imagem carregada para comparar dados EXIF.")
        return

    keys = ["A", "B", "C"][:len(valid_viewers)]
    card_infos = {k: ImageCardInfo(k, v) for k, v in zip(keys, valid_viewers)}
    compare_state = ExifCompareState(card_infos)

    popup = create_exif_window(parent)
    popup._photo_images = []

    # 1. Cards das imagens
    build_image_cards(popup, keys, card_infos, BORDER_COLORS, popup._photo_images)

    # 2. Barra de ações e filtros (definida após referências de callbacks)
    actions_bar = None
    table_view = None

    def on_state_changed(tags_to_sync):
        table_view.sync_rows(tags_to_sync)
        update_summary_ui()

    def on_filter_changed():
        visible = actions_bar.get_visible_tags()
        table_view.build_table_contents(visible)
        update_summary_ui()

    actions_bar = ExifActionsBar(
        popup,
        keys,
        compare_state,
        on_state_changed=on_state_changed,
        on_filter_changed=on_filter_changed,
    )

    def on_row_changed():
        update_summary_ui()

    # 3. Tabela Comparativa
    table_view = ExifTableView(
        popup,
        keys,
        card_infos,
        compare_state,
        on_row_changed=on_row_changed,
    )

    # 4. Barra Inferior de Resumo e Ações Finais
    bottom_frame = ctk.CTkFrame(
        popup,
        fg_color=COLOR_TOOLBAR_BG,
        corner_radius=CORNER_RADIUS,
        height=68,
    )
    bottom_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
    bottom_frame.pack_propagate(False)

    summary_container = tk.Frame(bottom_frame, bg=get_mode_color(COLOR_TOOLBAR_BG))
    summary_container.pack(side=tk.LEFT, padx=16, pady=8)

    tk.Label(
        summary_container,
        text="RESUMO DA OPERAÇÃO",
        font=("Segoe UI", 9, "bold"),
        fg=get_mode_color(COLOR_TEXT_MUTED),
        bg=get_mode_color(COLOR_TOOLBAR_BG),
        anchor="w",
    ).pack(anchor="w")

    lbl_summary_details = tk.Label(
        summary_container,
        text="0 campos selecionados  •  0 transferências programadas",
        font=("Segoe UI", 10),
        fg=get_mode_color(COLOR_TEXT_MAIN),
        bg=get_mode_color(COLOR_TOOLBAR_BG),
        anchor="w",
    )
    lbl_summary_details.pack(anchor="w")

    actions_container = tk.Frame(bottom_frame, bg=get_mode_color(COLOR_TOOLBAR_BG))
    actions_container.pack(side=tk.RIGHT, padx=16, pady=12)

    def _close_popup():
        try:
            table_view.unbind_mousewheel()
            if popup.state() != "zoomed":
                save_exif_geometry(popup.geometry())
        except Exception:
            pass
        popup.destroy()

    popup.protocol("WM_DELETE_WINDOW", _close_popup)
    popup.bind("<Escape>", lambda e: _close_popup())

    btn_cancel = ctk.CTkButton(
        actions_container,
        text="Cancelar",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=COLOR_BTN_ACTION_FG,
        hover_color=COLOR_BTN_ACTION_HOVER,
        text_color=COLOR_BTN_ACTION_TEXT,
        width=100,
        height=34,
        corner_radius=CORNER_RADIUS,
        command=_close_popup,
    )
    btn_cancel.pack(side=tk.LEFT, padx=(0, 10))

    btn_copy_save = ctk.CTkButton(
        actions_container,
        text="Copiar e Salvar",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=COLOR_PRIMARY,
        hover_color=COLOR_PRIMARY_HOVER,
        text_color=COLOR_PRIMARY_TEXT,
        width=135,
        height=34,
        corner_radius=CORNER_RADIUS,
    )
    btn_copy_save.pack(side=tk.LEFT)

    def update_summary_ui():
        summary = compare_state.compute_summary()
        sel = summary["selected_count"]
        trans = summary["transfers_count"]
        ow = summary["overwrites_count"]

        details = f"✓ {sel} campo(s) selecionado(s)   •   ↔ {trans} transferência(s) programada(s)"
        if ow > 0:
            details += f"   •   ⚠ {ow} valor(es) serão sobrescrito(s)"

        lbl_summary_details.configure(text=details)
        btn_copy_save.configure(state="normal" if trans > 0 else "disabled")

        for cat, tags in compare_state.categories.items():
            if cat in table_view.category_header_lbls:
                cat_sel = sum(1 for t in tags if compare_state.row_states[t].selected)
                is_col = table_view.category_collapsed.get(cat, False)
                table_view.category_header_lbls[cat].configure(
                    text=f"{'▶' if is_col else '▼'}  {cat} ({len(tags)} campos" + (f", {cat_sel} selecionados)" if cat_sel else ")")
                )

    def on_copy_and_save():
        summary = compare_state.compute_summary()
        if summary["transfers_count"] == 0:
            messagebox.showwarning("Aviso", "Nenhuma transferência válida está selecionada.")
            return

        ow = summary["overwrites_count"]
        msg = f"Confirma a execução de {summary['transfers_count']} transferência(s) de metadados EXIF?"
        if ow > 0:
            msg += f"\n\n⚠ ATENÇÃO: {ow} metadado(s) já existente(s) com valores diferentes serão sobrescritos nos arquivos de destino!"
        msg += "\n\nOs demais metadados originais de cada arquivo serão integralmente preservados."

        if not messagebox.askyesno("Confirmar Transferência EXIF", msg, parent=popup):
            return

        btn_copy_save.configure(state="disabled")
        btn_cancel.configure(state="disabled")
        popup.update()

        result = execute_planned_exif_transfers(compare_state)

        btn_copy_save.configure(state="normal")
        btn_cancel.configure(state="normal")

        if result["success"]:
            dest_names = ", ".join(result["modified_destinations"])
            messagebox.showinfo(
                "Sucesso",
                f"Metadados transferidos com sucesso!\n\n"
                f"Total de {result['transferred_count']} operação(ões) concluída(s) em:\n{dest_names}",
                parent=popup,
            )
            for card in card_infos.values():
                card._load_details()
            table_view.build_table_contents(actions_bar.get_visible_tags())
            update_summary_ui()
        else:
            err_msg = "\n".join(result["errors"]) if result["errors"] else "Erro desconhecido na gravação."
            messagebox.showerror("Erro na Transferência", f"Não foi possível concluir a operação:\n\n{err_msg}", parent=popup)

    btn_copy_save.configure(command=on_copy_and_save)

    popup.transient(parent)
    popup.grab_set()
    popup.update()

    init_w = table_view.canvas.winfo_width()
    if init_w > 50:
        table_view.apply_col_widths(init_w)

    table_view.build_table_contents(actions_bar.get_visible_tags())
    update_summary_ui()

    table_view.canvas.configure(scrollregion=table_view.canvas.bbox("all"))
    table_view.canvas.yview_moveto(0)
    popup.update()

    def _force_initial_repaint():
        try:
            w = table_view.canvas.winfo_width()
            if w > 50:
                table_view.apply_col_widths(w)
            table_view.canvas.configure(scrollregion=table_view.canvas.bbox("all"))
            table_view.canvas.yview_moveto(0.001)
            table_view.canvas.yview_moveto(0.0)
            table_view.scroll_content.update_idletasks()
        except Exception:
            pass

    popup.after(25, _force_initial_repaint)
    popup.after(60, _force_initial_repaint)