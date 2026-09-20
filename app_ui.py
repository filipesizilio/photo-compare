"""
================================================================================
Módulo: app_ui.py
Descrição: Construção da interface do usuário (barra de ferramentas, barra de
           status, layout dos visualizadores, organização das colunas).
================================================================================
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk

from app_config import (
    CORNER_RADIUS,
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
    COLOR_SYNC_LOCKED_FG,
    COLOR_SYNC_LOCKED_HOVER,
    COLOR_SYNC_UNLOCKED_FG,
    COLOR_SYNC_UNLOCKED_HOVER,
    save_appearance_mode,
    get_initial_appearance_mode,
)

from ui_tooltip import add_tooltip


class AppUI:
    """Constrói e gerencia a interface do usuário da aplicação."""

    def __init__(self, root, viewer1, viewer2, viewer3, callbacks):
        self.root = root
        self.callbacks = callbacks
        self.third_column_visible = False

        self._init_style()
        self._build_ui()

    @property
    def viewer1(self):
        return self.callbacks.get('viewer1')

    @property
    def viewer2(self):
        return self.callbacks.get('viewer2')

    @property
    def viewer3(self):
        return self.callbacks.get('viewer3')

    def _init_style(self):
        """Configurações visuais do ttk para combinar com o tema escuro."""
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

    def _build_ui(self):
        # 1. Barra de ferramentas superior (CTkFrame com suporte a modo claro/escuro)
        self.toolbar = ctk.CTkFrame(
            self.root,
            fg_color=COLOR_TOOLBAR_BG,
            corner_radius=0,
            height=50
        )
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        # Logotipo / Nome do App
        lbl_brand = ctk.CTkLabel(
            self.toolbar,
            text="Photo Compare",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLOR_BRAND_TEXT
        )
        lbl_brand.pack(side=tk.LEFT, padx=(12, 14), pady=6)

        # Divisor visual
        sep1 = ctk.CTkFrame(
            self.toolbar,
            fg_color=COLOR_SEPARATOR,
            corner_radius=0,
            width=1,
            height=28
        )
        sep1.pack(side=tk.LEFT, padx=(0, 12), fill=tk.Y, pady=10)

        # Botão de Trava de Sincronização: ícone "🔒" com tooltip
        self.btn_sync = ctk.CTkButton(
            self.toolbar,
            text="🔒",
            width=38,
            height=34,
            corner_radius=CORNER_RADIUS,
            font=ctk.CTkFont(size=15),
            fg_color=COLOR_SYNC_LOCKED_FG,
            hover_color=COLOR_SYNC_LOCKED_HOVER,
            command=self.callbacks['toggle_sync']
        )
        self.btn_sync.pack(side=tk.LEFT, padx=(0, 8))
        add_tooltip(self.btn_sync, "Alternar sincronização de pan e zoom [Espaço]")

        # Segmented control para quantidade de imagens (2 ou 3)
        self.seg_qtd_imagens = ctk.CTkSegmentedButton(
            self.toolbar,
            values=["2 imagens", "3 imagens"],
            command=self._on_qtd_imagens_change,
            corner_radius=CORNER_RADIUS,
            width=170,
            height=32
        )
        self.seg_qtd_imagens.set("3 imagens" if self.third_column_visible else "2 imagens")
        self.seg_qtd_imagens.pack(side=tk.LEFT, padx=(0, 10))
        add_tooltip(self.seg_qtd_imagens, "Alternar entre 2 e 3 colunas de comparação")

        # Compatibilidade com referências existentes a self.btn_toggle_3rd
        self.btn_toggle_3rd = self.seg_qtd_imagens

        # Botão Ajustar Todas (ícone ⛶ com fonte Segoe UI Symbol)
        self.btn_fit_all = ctk.CTkButton(
            self.toolbar,
            text="⛶",
            width=38,
            height=34,
            corner_radius=CORNER_RADIUS,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=16, weight="bold"),
            fg_color=COLOR_TRANSPARENT,
            hover_color=COLOR_HOVER_MUTED,
            text_color=COLOR_TEXT_MAIN,
            command=self.callbacks['fit_all_to_window']
        )
        self.btn_fit_all.pack(side=tk.LEFT, padx=(4, 2))
        add_tooltip(self.btn_fit_all, "Ajustar todas as imagens à tela [F]")

        # Botão 100% Todas (ícone 1:1)
        self.btn_reset_all = ctk.CTkButton(
            self.toolbar,
            text="1:1",
            width=38,
            height=34,
            corner_radius=CORNER_RADIUS,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_TRANSPARENT,
            hover_color=COLOR_HOVER_MUTED,
            text_color=COLOR_TEXT_MAIN,
            command=self.callbacks['reset_all_100']
        )
        self.btn_reset_all.pack(side=tk.LEFT, padx=2)
        add_tooltip(self.btn_reset_all, "Redefinir todas para zoom 100% (1:1)")

        # Botão Alinhar à Imagem A (ícone ⇄ com fonte Segoe UI Symbol)
        self.btn_align_panel1 = ctk.CTkButton(
            self.toolbar,
            text="⇄",
            width=38,
            height=34,
            corner_radius=CORNER_RADIUS,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=17, weight="bold"),
            fg_color=COLOR_TRANSPARENT,
            hover_color=COLOR_HOVER_MUTED,
            text_color=COLOR_TEXT_MAIN,
            command=self.callbacks['align_to_first_panel']
        )
        self.btn_align_panel1.pack(side=tk.LEFT, padx=2)
        add_tooltip(self.btn_align_panel1, "Alinhar pan e zoom de todas as imagens com a Imagem A")

        # Botão Comparar EXIF (ícone ℹ de informação/metadados)
        self.btn_exif_compare = ctk.CTkButton(
            self.toolbar,
            text="exif",
            width=38,
            height=34,
            corner_radius=CORNER_RADIUS,
            font=ctk.CTkFont(family="Segoe UI Symbol", size=14, weight="normal"),
            fg_color=COLOR_TRANSPARENT,
            hover_color=COLOR_HOVER_MUTED,
            text_color=COLOR_TEXT_MAIN,
            command=self.callbacks['show_exif_comparison']
        )
        self.btn_exif_compare.pack(side=tk.LEFT, padx=3)
        add_tooltip(self.btn_exif_compare, "Metadados e comparação EXIF")

        # Segmented control de tema (Sol / Lua / Computador)
        self.seg_theme = ctk.CTkSegmentedButton(
            self.toolbar,
            values=["☀", "🌙", "💻"],
            command=self._on_theme_mode_change,
            corner_radius=CORNER_RADIUS,
            width=108,
            height=32,
            font=ctk.CTkFont(size=13),
        )
        active_mode = get_initial_appearance_mode()
        self.seg_theme.set({"light": "☀", "dark": "🌙", "system": "💻"}.get(active_mode, "💻"))
        self.seg_theme.pack(side=tk.RIGHT, padx=(0, 10))
        add_tooltip(self.seg_theme, "Modo de aparência: Claro (☀), Escuro (🌙) ou Sistema (💻)")
        self.btn_theme = self.seg_theme

        # 2. Barra de status inferior
        self.statusbar = ctk.CTkFrame(
            self.root,
            fg_color=COLOR_STATUSBAR_BG,
            corner_radius=0,
            height=28
        )
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.statusbar,
            text="Pronto. Selecione até 3 imagens ou arraste arquivos do Windows Explorer para cá.",
            font=ctk.CTkFont(size=11),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_status.pack(side=tk.LEFT, padx=(12, 0))

        # Link clicável para o repositório GitHub
        self.lbl_github = ctk.CTkLabel(
            self.statusbar,
            text="🌐 GitHub: Photo-Compare",
            font=ctk.CTkFont(size=11, underline=True),
            text_color=COLOR_LINK_TEXT,
            cursor="hand2"
        )
        self.lbl_github.pack(side=tk.RIGHT, padx=(0, 12))
        def _on_github_click(_event=None):
            if 'open_github' in self.callbacks:
                self.callbacks['open_github']()

        self.lbl_github.bind("<Button-1>", _on_github_click)
        try:
            tk.Frame.bind(self.lbl_github, "<Button-1>", _on_github_click)
        except Exception:
            pass
        self.lbl_github.bind("<Enter>", lambda e: self.lbl_github.configure(text_color=COLOR_LINK_HOVER))
        self.lbl_github.bind("<Leave>", lambda e: self.lbl_github.configure(text_color=COLOR_LINK_TEXT))
        add_tooltip(self.lbl_github, "Abrir repositório no GitHub")

        self._update_sync_button_style()

        # 3. Área central com colunas de comparação
        self.columns_container = ctk.CTkFrame(
            self.root,
            fg_color=COLOR_COLUMNS_CONTAINER_BG,
            corner_radius=0
        )
        self.columns_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.columns_container.rowconfigure(0, weight=1)

        # NOTA: _arrange_columns() será chamado manualmente após os visualizadores serem criados

    def _arrange_columns(self):
        """Organiza as colunas em grid proporcional de acordo com a visibilidade."""
        # Limpa layout anterior e reseta colunas
        for key in ('viewer1', 'viewer2', 'viewer3'):
            self.callbacks[key].grid_forget()
        for i in range(3):
            self.columns_container.columnconfigure(i, weight=0, uniform="")

        active_keys = ('viewer1', 'viewer2', 'viewer3') if self.third_column_visible else ('viewer1', 'viewer2')
        group = f"cols{len(active_keys)}"
        for i, v_key in enumerate(active_keys):
            self.columns_container.columnconfigure(i, weight=1, uniform=group)
            self.callbacks[v_key].grid(row=0, column=i, sticky="nsew", padx=2, pady=2)

    def _on_theme_mode_change(self, valor):
        """Altera o modo de aparência para Claro, Escuro ou Sistema."""
        novo_modo = {"☀": "light", "🌙": "dark", "💻": "system"}.get(valor, "system")
        ctk.set_appearance_mode(novo_modo)
        save_appearance_mode(novo_modo)
        for key in ('viewer1', 'viewer2', 'viewer3'):
            viewer = self.callbacks.get(key)
            if viewer and hasattr(viewer, "update_appearance_mode"):
                viewer.update_appearance_mode()

    def _toggle_theme(self):
        """Alterna ciclicamente entre os modos Claro, Escuro e Sistema."""
        curr = self.seg_theme.get() if hasattr(self, "seg_theme") else "💻"
        nxt = {"☀": "🌙", "🌙": "💻", "💻": "☀"}.get(curr, "☀")
        if hasattr(self, "seg_theme"):
            self.seg_theme.set(nxt)
        self._on_theme_mode_change(nxt)

    def _on_qtd_imagens_change(self, valor):
        """Roteia alteração do segmented control para toggle_third_column evitando loops."""
        quer_tres = (valor == "3 imagens")
        if quer_tres != self.third_column_visible:
            self.callbacks['toggle_third_column']()

    def _update_sync_button_style(self):
        """Atualiza a aparência do botão de trava de sincronização (símbolo 🔒 ou 🔓)."""
        is_locked = self.callbacks.get('sync_locked', True)
        if is_locked:
            self.btn_sync.configure(
                text="🔒",
                fg_color=COLOR_SYNC_LOCKED_FG,
                hover_color=COLOR_SYNC_LOCKED_HOVER
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.configure(
                    text="Sincronização ativada (🔒): pan e zoom aplicados em uma imagem moverão as outras."
                )
        else:
            self.btn_sync.configure(
                text="🔓",
                fg_color=COLOR_SYNC_UNLOCKED_FG,
                hover_color=COLOR_SYNC_UNLOCKED_HOVER
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.configure(
                    text="Sincronização destravada (🔓): ajuste cada imagem individualmente para alinhamento."
                )

    def update_sync_button(self, sync_locked):
        """Atualiza o estado do botão de sincronização."""
        self.callbacks['sync_locked'] = sync_locked
        self._update_sync_button_style()

    def update_third_column_button(self, visible):
        """Atualiza o botão/segmented control da terceira coluna."""
        self.third_column_visible = visible
        if hasattr(self, "seg_qtd_imagens"):
            val = "3 imagens" if visible else "2 imagens"
            if self.seg_qtd_imagens.get() != val:
                self.seg_qtd_imagens.set(val)

    def set_status(self, text):
        """Atualiza o texto da barra de status."""
        if hasattr(self, "lbl_status"):
            self.lbl_status.configure(text=text)