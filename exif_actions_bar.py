"""
================================================================================
Módulo: exif_actions_bar.py
Descrição: Barra de ações globais, filtros e busca textual para a janela EXIF.
================================================================================
"""

import tkinter as tk
import customtkinter as ctk

from app_config import (
    CORNER_RADIUS,
    COLOR_TOOLBAR_BG,
    COLOR_TEXT_MAIN,
    COLOR_TEXT_MUTED,
    COLOR_BTN_ACTION_FG,
    COLOR_BTN_ACTION_HOVER,
    COLOR_BTN_ACTION_TEXT,
)


class ExifActionsBar:
    """Gerencia a barra superior de ações em lote, filtros e pesquisa."""

    def __init__(self, parent, keys, compare_state, on_state_changed, on_filter_changed):
        self.parent = parent
        self.keys = keys
        self.compare_state = compare_state
        self.on_state_changed = on_state_changed
        self.on_filter_changed = on_filter_changed

        self._build_ui()

    def _build_ui(self):
        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=COLOR_TOOLBAR_BG,
            corner_radius=CORNER_RADIUS,
            height=48,
        )
        self.frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 6))
        self.frame.pack_propagate(False)

        # Texto: "Tudo:"
        ctk.CTkLabel(
            self.frame,
            text="Tudo:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        ).pack(side=tk.LEFT, padx=(12, 6))

        # Combobox "Copiar de"
        ctk.CTkLabel(
            self.frame,
            text="Copiar de:",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side=tk.LEFT, padx=(4, 4))

        source_options = ["Nenhuma"] + [f"Imagem {k}" for k in self.keys]
        self.combo_source = ctk.CTkComboBox(
            self.frame,
            values=source_options,
            width=115,
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=CORNER_RADIUS,
            state="readonly",
            command=self._on_source_combo_changed,
        )
        self.combo_source.set("Nenhuma")
        self.combo_source.pack(side=tk.LEFT, padx=(0, 8))

        # Combobox "Para"
        ctk.CTkLabel(
            self.frame,
            text="Para:",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED,
        ).pack(side=tk.LEFT, padx=(4, 4))

        self.combo_dest = ctk.CTkComboBox(
            self.frame,
            values=["Todos os destinos válidos"],
            width=170,
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=CORNER_RADIUS,
            state="readonly",
            command=self._on_dest_combo_changed,
        )
        self.combo_dest.set("Todos os destinos válidos")
        self.combo_dest.pack(side=tk.LEFT, padx=(0, 12))

        # Checkbox "Marcar Todos"
        self.chk_select_all_var = tk.BooleanVar(value=False)
        self.chk_select_all = ctk.CTkCheckBox(
            self.frame,
            text="Marcar Todos",
            variable=self.chk_select_all_var,
            font=ctk.CTkFont(size=11, weight="bold"),
            corner_radius=4,
            command=self._on_select_all_toggle,
        )
        self.chk_select_all.pack(side=tk.LEFT, padx=(0, 10))

        # Botão "Limpar"
        self.btn_clear = ctk.CTkButton(
            self.frame,
            text="Limpar",
            font=ctk.CTkFont(size=11),
            fg_color=COLOR_BTN_ACTION_FG,
            hover_color=COLOR_BTN_ACTION_HOVER,
            text_color=COLOR_BTN_ACTION_TEXT,
            width=70,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self._on_clear_clicked,
        )
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 16))

        # Separador sutil
        tk.Frame(self.frame, bg="#3f3f46", width=1, height=24).pack(side=tk.LEFT, padx=(0, 16))

        # Menu / Combobox "Filtros:"
        ctk.CTkLabel(
            self.frame,
            text="Filtro:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXT_MAIN,
        ).pack(side=tk.LEFT, padx=(0, 4))

        filter_options = [
            "Todos",
            "Somente diferentes",
            "Somente presentes em todas",
            "Somente ausentes em alguma",
            "Somente selecionados",
        ]
        self.combo_filter = ctk.CTkComboBox(
            self.frame,
            values=filter_options,
            width=190,
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=CORNER_RADIUS,
            state="readonly",
            command=lambda e: self.on_filter_changed(),
        )
        self.combo_filter.set("Todos")
        self.combo_filter.pack(side=tk.LEFT, padx=(0, 10))

        # Campo de busca rápida de tags
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.on_filter_changed())
        self.entry_search = ctk.CTkEntry(
            self.frame,
            placeholder_text="🔍 Buscar campo...",
            textvariable=self.search_var,
            width=150,
            height=28,
            font=ctk.CTkFont(size=11),
            corner_radius=CORNER_RADIUS,
        )
        self.entry_search.pack(side=tk.RIGHT, padx=12)

    def get_visible_tags(self):
        """Filtra as tags de acordo com o filtro selecionado e a busca textual."""
        query = self.search_var.get().strip().lower()
        filter_mode = self.combo_filter.get()

        res = []
        for tag in sorted(self.compare_state.all_tags):
            if query and query not in tag.lower():
                continue
            if filter_mode == "Somente diferentes" and not self.compare_state.is_tag_different(tag):
                continue
            if filter_mode == "Somente presentes em todas" and not self.compare_state.is_present_in_all(tag):
                continue
            if filter_mode == "Somente ausentes em alguma" and not self.compare_state.is_absent_in_any(tag):
                continue
            if filter_mode == "Somente selecionados" and not self.compare_state.row_states[tag].selected:
                continue
            res.append(tag)
        return res

    def _on_source_combo_changed(self, *args):
        src_raw = self.combo_source.get()
        source_key = src_raw.replace("Imagem ", "").strip()

        if source_key in self.keys:
            valid_dests = [k for k in self.keys if k != source_key]
            opts = ["Todos os destinos válidos"] + [f"Imagem {k}" for k in valid_dests]
        else:
            opts = ["Todos os destinos válidos"]
        self.combo_dest.configure(values=opts)
        self.combo_dest.set("Todos os destinos válidos")
        self._apply_global_source_dest()

    def _on_dest_combo_changed(self, *args):
        self._apply_global_source_dest()

    def _apply_global_source_dest(self):
        src_raw = self.combo_source.get()
        dest_raw = self.combo_dest.get()

        source_key = src_raw.replace("Imagem ", "").strip()
        dest_key = "ALL"
        if "Imagem " in dest_raw:
            dest_key = dest_raw.replace("Imagem ", "").strip()

        visible_tags = self.get_visible_tags()
        self.compare_state.apply_global_source_dest(source_key, dest_key, visible_tags)

        if source_key in self.keys:
            self.compare_state.set_all_selected(True, visible_tags)

        self.on_state_changed(visible_tags)

    def _on_select_all_toggle(self):
        val = self.chk_select_all_var.get()
        visible = self.get_visible_tags()
        self.compare_state.set_all_selected(val, visible)
        self.on_state_changed(visible)

    def _on_clear_clicked(self):
        self.compare_state.clear_all()
        self.chk_select_all_var.set(False)
        self.combo_source.set("Nenhuma")
        self.combo_dest.set("Todos os destinos válidos")
        self.on_state_changed(list(self.compare_state.all_tags))

