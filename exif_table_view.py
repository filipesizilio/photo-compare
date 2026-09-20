"""
================================================================================
Módulo: exif_table_view.py
Descrição: Tabela com rolagem sincronizada, categorias recolhíveis e células de
           metadados para comparação de dados EXIF.
================================================================================
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from app_config import (
    CORNER_RADIUS,
    COLOR_VIEWER_BG,
    COLOR_VIEWER_HEADER,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    COLOR_BORDER_IMAGE_A,
    COLOR_BORDER_IMAGE_B,
    COLOR_BORDER_IMAGE_C,
    get_mode_color,
)
from ui_tooltip import add_tooltip

BORDER_COLORS = {
    "A": COLOR_BORDER_IMAGE_A,
    "B": COLOR_BORDER_IMAGE_B,
    "C": COLOR_BORDER_IMAGE_C,
}


class ExifTableView:
    """Gerencia a tabela comparativa com rolagem vertical e colunas sincronizadas."""

    def __init__(self, parent, keys, card_infos, compare_state, on_row_changed):
        self.parent = parent
        self.keys = keys
        self.card_infos = card_infos
        self.compare_state = compare_state
        self.on_row_changed = on_row_changed

        self.row_widgets = {}
        self.category_collapsed = {cat: False for cat in compare_state.categories.keys()}
        self.category_header_lbls = {}
        self.header_col_frames = []
        self.all_row_col_frames = []

        self._build_table_structure()

    def _add_header_col(self, col_idx, text, fg_color, padx):
        hf = tk.Frame(self.table_header, bg=get_mode_color(COLOR_VIEWER_HEADER), height=34)
        hf.grid(row=0, column=col_idx, sticky="nsew", padx=padx)
        hf.pack_propagate(False)
        tk.Label(
            hf, text=text, font=("Segoe UI", 9, "bold"),
            bg=get_mode_color(COLOR_VIEWER_HEADER), fg=fg_color, anchor="w",
        ).pack(side=tk.LEFT, padx=(2, 0), pady=6)
        self.header_col_frames.append(hf)

    def _build_table_structure(self):
        self.container = ctk.CTkFrame(
            self.parent, fg_color=COLOR_VIEWER_BG, corner_radius=CORNER_RADIUS,
            border_width=1, border_color=("#d4d4d8", "#27272a"),
        )
        self.container.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 6))
        self.container.rowconfigure(0, weight=0)
        self.container.rowconfigure(1, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=0)

        # Cabeçalho da Tabela
        self.table_header = tk.Frame(self.container, bg=get_mode_color(COLOR_VIEWER_HEADER), height=34)
        self.table_header.grid(row=0, column=0, sticky="ew", padx=(2, 0), pady=(2, 0))
        self.table_header.pack_propagate(False)

        self.header_spacer = tk.Frame(self.container, bg=get_mode_color(COLOR_VIEWER_HEADER), width=16, height=34)
        self.header_spacer.grid(row=0, column=1, sticky="nsew", pady=(2, 0))

        # Colunas de Cabeçalho
        self._add_header_col(0, "CAMPO EXIF", get_mode_color(COLOR_TEXT_MAIN), (10, 4))
        self._add_header_col(1, "COPIAR DE", get_mode_color(COLOR_TEXT_MAIN), (6, 4))
        for idx, k in enumerate(self.keys):
            accent = get_mode_color(BORDER_COLORS.get(k, COLOR_BORDER_IMAGE_A))
            self._add_header_col(2 + idx, f"IMAGEM {k}", accent, (6, 4))

        # Canvas e scrollbar
        self.canvas = tk.Canvas(self.container, bg=get_mode_color(COLOR_VIEWER_BG), highlightthickness=0)
        self.scrollbar_y = ttk.Scrollbar(self.container, orient="vertical", command=self.canvas.yview)
        self.scroll_content = tk.Frame(self.canvas, bg=get_mode_color(COLOR_VIEWER_BG))
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scroll_content, anchor="nw")

        self.canvas.bind("<Configure>", lambda e: self.apply_col_widths(e.width) if e.width > 50 else None)
        self.scroll_content.bind(
            "<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.configure(xscrollcommand=None, yscrollcommand=self.scrollbar_y.set)

        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(2, 0), pady=2)
        self.scrollbar_y.grid(row=1, column=1, sticky="ns", pady=2)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        delta = -1 * (event.delta // 120) if event.delta else 0
        self.canvas.yview_scroll(delta, "units")

    def unbind_mousewheel(self):
        try:
            self.canvas.unbind_all("<MouseWheel>")
        except Exception:
            pass

    def compute_col_widths(self, total_w):
        num_imgs = len(self.keys)
        padding_sum = 44 if num_imgs == 2 else 54
        avail = max(600, total_w - padding_sum)
        w_copy = 125
        if num_imgs == 2:
            w_field = max(260, int(avail * 0.28))
            rem = max(360, avail - w_copy - w_field)
            w_img = rem // 2
            return [w_field, w_copy, w_img, rem - w_img]
        w_field = max(230, int(avail * 0.23))
        rem = max(450, avail - w_copy - w_field)
        w_img = rem // 3
        return [w_field, w_copy, w_img, w_img, rem - (2 * w_img)]

    def apply_col_widths(self, total_w):
        if total_w < 400:
            return
        col_widths = self.compute_col_widths(total_w)
        for c, w in enumerate(col_widths):
            self.table_header.grid_columnconfigure(c, minsize=w, weight=0)
            self.scroll_content.grid_columnconfigure(c, minsize=w, weight=0)
        for c, hf in enumerate(self.header_col_frames):
            hf.configure(width=col_widths[c])
        for row_fs in self.all_row_col_frames:
            for c, f in enumerate(row_fs):
                f.configure(width=col_widths[c])
        self.canvas.itemconfig(self.canvas_window, width=total_w)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def toggle_category(self, cat_name, visible_tags):
        self.category_collapsed[cat_name] = not self.category_collapsed[cat_name]
        self.build_table_contents(visible_tags)

    def build_table_contents(self, visible_tags):
        for child in self.scroll_content.winfo_children():
            child.destroy()
        self.row_widgets.clear()
        self.category_header_lbls.clear()
        self.all_row_col_frames.clear()

        vis_set = set(visible_tags)
        total_cols = 2 + len(self.keys)
        current_row = 0

        for cat_name, cat_tags in self.compare_state.categories.items():
            tags_to_show = [t for t in cat_tags if t in vis_set]
            if not tags_to_show:
                continue

            current_row = self._render_category_header(cat_name, cat_tags, visible_tags, total_cols, current_row)
            if self.category_collapsed.get(cat_name, False):
                continue

            for tag_name in tags_to_show:
                current_row = self._render_tag_row(tag_name, current_row)

        curr_w = self.canvas.winfo_width()
        if curr_w > 50:
            self.apply_col_widths(curr_w)

    def _render_category_header(self, cat_name, cat_tags, visible_tags, total_cols, current_row):
        cat_header = tk.Frame(
            self.scroll_content, bg=get_mode_color(COLOR_VIEWER_HEADER), height=30, cursor="hand2",
        )
        cat_header.grid(row=current_row, column=0, columnspan=total_cols, sticky="ew", padx=2, pady=(6, 2))
        cat_header.pack_propagate(False)

        cat_sel = sum(1 for t in cat_tags if self.compare_state.row_states[t].selected)
        is_col = self.category_collapsed.get(cat_name, False)
        cat_title = f"{'▶' if is_col else '▼'}  {cat_name} ({len(cat_tags)} campos" + (f", {cat_sel} selecionados)" if cat_sel else ")")

        cat_lbl = tk.Label(
            cat_header, text=cat_title, font=("Segoe UI", 9, "bold"),
            fg="#60a5fa" if cat_name != "Outros" else get_mode_color(COLOR_TEXT_MUTED),
            bg=get_mode_color(COLOR_VIEWER_HEADER), anchor="w", cursor="hand2",
        )
        cat_lbl.pack(side=tk.LEFT, padx=10)
        self.category_header_lbls[cat_name] = cat_lbl

        cat_header.bind("<Button-1>", lambda e, c=cat_name: self.toggle_category(c, visible_tags))
        cat_lbl.bind("<Button-1>", lambda e, c=cat_name: self.toggle_category(c, visible_tags))
        return current_row + 1

    def _render_tag_row(self, tag_name, current_row):
        row_state = self.compare_state.row_states[tag_name]
        tag_values = self.compare_state.get_tag_values(tag_name)
        is_different = self.compare_state.is_tag_different(tag_name)
        row_bg = get_mode_color(COLOR_VIEWER_BG)

        # Coluna 0: Nome do Campo EXIF + Marcador de diferença
        col0_frame = tk.Frame(self.scroll_content, bg=row_bg, height=30)
        col0_frame.grid(row=current_row, column=0, sticky="nsew", padx=(10, 4), pady=1)
        col0_frame.pack_propagate(False)

        diff_marker = "≠ " if is_different else "   "
        diff_color = "#f59e0b" if is_different else get_mode_color(COLOR_TEXT_MUTED)
        tk.Label(col0_frame, text=diff_marker, font=("Segoe UI", 9, "bold"), fg=diff_color, bg=row_bg).pack(side=tk.LEFT, padx=(2, 0))

        lbl_tag = tk.Label(
            col0_frame, text=tag_name, font=("Segoe UI", 9),
            fg=get_mode_color(COLOR_TEXT_MAIN), bg=row_bg, anchor="w"
        )
        lbl_tag.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 4))
        if len(tag_name) > 28:
            add_tooltip(lbl_tag, tag_name)

        # Coluna 1: Combobox "Copiar de"
        col1_frame = tk.Frame(self.scroll_content, bg=row_bg, height=30)
        col1_frame.grid(row=current_row, column=1, sticky="nsew", padx=(6, 4), pady=1)
        col1_frame.pack_propagate(False)

        valid_src_keys = [k for k in self.keys if tag_name in self.card_infos[k].exif_data]
        combo_src_values = ["—"] + [f"Imagem {k}" for k in valid_src_keys]

        combo_src = ctk.CTkComboBox(
            col1_frame, values=combo_src_values, width=105, height=24, font=ctk.CTkFont(size=10),
            corner_radius=4, state="readonly" if valid_src_keys else "disabled",
            command=lambda val, t=tag_name: self._on_row_source_changed(t, val)
        )
        combo_src.set(f"Imagem {row_state.source}" if row_state.source in valid_src_keys else "—")
        combo_src.pack(side=tk.LEFT, padx=(2, 0), pady=1)

        line_dict = {"combo_source": combo_src}
        current_row_frames = [col0_frame, col1_frame]

        # Colunas 2..N: Imagens com Checkbox (16x16) e Valor
        for idx, k in enumerate(self.keys):
            cell_frame, dest_var, dest_chk = self._render_cell(
                tag_name, k, tag_values.get(k, "—"), row_state, row_bg, current_row, 2 + idx
            )
            line_dict[f"dest_var_{k}"] = dest_var
            line_dict[f"dest_chk_{k}"] = dest_chk
            current_row_frames.append(cell_frame)

        self.all_row_col_frames.append(current_row_frames)
        self.row_widgets[tag_name] = line_dict
        self.sync_row_ui(tag_name)
        return current_row + 1

    def _render_cell(self, tag_name, k, val_str, row_state, row_bg, current_row, col_idx):
        cell_frame = tk.Frame(self.scroll_content, bg=row_bg, height=30)
        cell_frame.grid(row=current_row, column=col_idx, sticky="nsew", padx=(6, 4), pady=1)
        cell_frame.pack_propagate(False)

        dest_var = tk.BooleanVar(value=k in row_state.destinations)
        dest_chk = ctk.CTkCheckBox(
            cell_frame, text="", variable=dest_var,
            width=16, height=16, checkbox_width=16, checkbox_height=16, corner_radius=3,
            command=lambda t=tag_name, dest=k, v=dest_var: self._on_row_dest_toggle(t, dest, v.get())
        )
        dest_chk.pack(side=tk.LEFT, padx=(2, 6), pady=3)

        has_val = tag_name in self.card_infos[k].exif_data
        val_color = get_mode_color(COLOR_TEXT_MAIN) if has_val else get_mode_color(COLOR_TEXT_MUTED)
        lbl_val = tk.Label(
            cell_frame, text=val_str, font=("Segoe UI", 9), fg=val_color, bg=row_bg, anchor="w", justify=tk.LEFT,
        )
        lbl_val.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=3)
        if len(val_str) > 24:
            add_tooltip(lbl_val, val_str)

        return cell_frame, dest_var, dest_chk

    def _on_row_source_changed(self, tag_name, new_source_str):
        row = self.compare_state.row_states[tag_name]
        chosen = new_source_str.replace("Imagem ", "").strip()
        if chosen not in self.keys:
            row.source = ""
            row.destinations.clear()
            row.selected = False
        else:
            row.source = chosen
            row.destinations.discard(chosen)
            if not row.destinations:
                row.destinations = {k for k in self.keys if k != chosen}
            row.selected = bool(row.destinations)

        self.sync_row_ui(tag_name)
        self.on_row_changed()

    def _on_row_dest_toggle(self, tag_name, dest_key, val):
        row = self.compare_state.row_states[tag_name]
        if val:
            row.destinations.add(dest_key)
            row.selected = True
        else:
            row.destinations.discard(dest_key)
            row.selected = bool(row.destinations)

        self.sync_row_ui(tag_name)
        self.on_row_changed()

    def sync_row_ui(self, tag_name):
        widgets = self.row_widgets.get(tag_name)
        if not widgets:
            return

        row = self.compare_state.row_states[tag_name]
        expected_src = f"Imagem {row.source}" if row.source in self.keys else "—"
        if widgets["combo_source"].get() != expected_src:
            widgets["combo_source"].set(expected_src)

        for k in self.keys:
            chk_var = widgets[f"dest_var_{k}"]
            chk_widget = widgets[f"dest_chk_{k}"]

            if k == row.source or not row.source:
                chk_var.set(False)
                chk_widget.configure(state="disabled")
            else:
                chk_widget.configure(state="normal")
                chk_var.set(k in row.destinations)

    def sync_rows(self, tags):
        for t in tags:
            self.sync_row_ui(t)

