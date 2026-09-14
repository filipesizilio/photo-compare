"""
================================================================================
Módulo: app_ui.py
Descrição: Construção da interface do usuário (barra de ferramentas, barra de
           status, layout dos visualizadores, organização das colunas).
================================================================================
"""

import tkinter as tk
from tkinter import ttk


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
        # 1. Barra de ferramentas superior
        self.toolbar = tk.Frame(self.root, bg="#18181b", height=50, padx=12, pady=6)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        # Logotipo / Nome do App
        lbl_brand = tk.Label(
            self.toolbar,
            text="Photo Compare",
            font=("Segoe UI", 12, "bold"),
            fg="#f4f4f5",
            bg="#18181b"
        )
        lbl_brand.pack(side=tk.LEFT, padx=(0, 16))

        # Divisor visual
        sep1 = tk.Frame(self.toolbar, bg="#27272a", width=1, height=28)
        sep1.pack(side=tk.LEFT, padx=(0, 16), fill=tk.Y, pady=4)

        # Botão de Trava de Sincronização: apenas o símbolo de cadeado "🔒"
        self.btn_sync = tk.Button(
            self.toolbar,
            text="🔒",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            width=3,
            pady=4,
            cursor="hand2",
            command=self.callbacks['toggle_sync']
        )
        self.btn_sync.pack(side=tk.LEFT, padx=(0, 10))

        # Botão para alternar 3ª Coluna
        self.btn_toggle_3rd = tk.Button(
            self.toolbar,
            text="➕ 3ª Imagem",
            font=("Segoe UI", 9, "bold"),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.callbacks['toggle_third_column']
        )
        self.btn_toggle_3rd.pack(side=tk.LEFT, padx=(0, 10))

        # Divisor visual
        sep2 = tk.Frame(self.toolbar, bg="#27272a", width=1, height=28)
        sep2.pack(side=tk.LEFT, padx=(0, 16), fill=tk.Y, pady=4)

        # Botão Ajustar Todas
        self.btn_fit_all = tk.Button(
            self.toolbar,
            text="⤢ Ajustar [Todas]",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.callbacks['fit_all_to_window']
        )
        self.btn_fit_all.pack(side=tk.LEFT, padx=3)

        # Botão 100% Todas
        self.btn_reset_all = tk.Button(
            self.toolbar,
            text="1:1 [Todas]",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.callbacks['reset_all_100']
        )
        self.btn_reset_all.pack(side=tk.LEFT, padx=3)

        # Botão Alinhar ao Painel 1
        self.btn_align_panel1 = tk.Button(
            self.toolbar,
            text="↙ Alinhar [a Imagem 1]",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.callbacks['align_to_first_panel']
        )
        self.btn_align_panel1.pack(side=tk.LEFT, padx=3)

        # Botão Comparar EXIF
        self.btn_exif_compare = tk.Button(
            self.toolbar,
            text="📋 EXIF",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.callbacks['show_exif_comparison']
        )
        self.btn_exif_compare.pack(side=tk.LEFT, padx=3)

        # Dica rápida no lado direito
        lbl_hint = tk.Label(
            self.toolbar,
            text="Atalho: [Espaço] Sincronizar • [F] Ajustar • Arraste arquivos aqui",
            font=("Segoe UI", 9),
            fg="#71717a",
            bg="#18181b"
        )
        lbl_hint.pack(side=tk.RIGHT, padx=4)

        # 2. Barra de status inferior
        self.statusbar = tk.Frame(self.root, bg="#18181b", height=26, padx=12)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)

        self.lbl_status = tk.Label(
            self.statusbar,
            text="Pronto. Selecione até 3 imagens ou arraste arquivos do Windows Explorer para cá.",
            font=("Segoe UI", 8),
            fg="#71717a",
            bg="#18181b"
        )
        self.lbl_status.pack(side=tk.LEFT)

        # Link clicável para o repositório GitHub
        self.lbl_github = tk.Label(
            self.statusbar,
            text="🌐 GitHub: Photo-Compare",
            font=("Segoe UI", 8, "underline"),
            fg="#60a5fa",
            bg="#18181b",
            cursor="hand2"
        )
        self.lbl_github.pack(side=tk.RIGHT)
        self.lbl_github.bind(
            "<Button-1>",
            lambda e: self.callbacks['open_github']
        )
        self.lbl_github.bind("<Enter>", lambda e: self.lbl_github.config(fg="#93c5fd"))
        self.lbl_github.bind("<Leave>", lambda e: self.lbl_github.config(fg="#60a5fa"))

        self._update_sync_button_style()

        # 3. Área central com colunas de comparação
        self.columns_container = tk.Frame(self.root, bg="#09090b")
        self.columns_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.columns_container.rowconfigure(0, weight=1)

        # NOTA: _arrange_columns() será chamado manualmente após os visualizadores serem criados

    def _arrange_columns(self):
        """Organiza as colunas em grid proporcional de acordo com a visibilidade."""
        # Limpa layout anterior
        self.callbacks['viewer1'].grid_forget()
        self.callbacks['viewer2'].grid_forget()
        self.callbacks['viewer3'].grid_forget()

        # Reseta configuração de colunas para evitar resíduos de uniform group
        for i in range(3):
            self.columns_container.columnconfigure(i, weight=0, uniform="")

        if not self.third_column_visible:
            # Apenas 2 colunas: dividem o espaço 50/50
            self.columns_container.columnconfigure(0, weight=1, uniform="cols2")
            self.columns_container.columnconfigure(1, weight=1, uniform="cols2")
            # Coluna 2 fica com weight=0 e sem uniform group
            self.columns_container.columnconfigure(2, weight=0, uniform="")

            self.callbacks['viewer1'].grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.callbacks['viewer2'].grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        else:
            # 3 colunas: dividem o espaço 33/33/33
            self.columns_container.columnconfigure(0, weight=1, uniform="cols3")
            self.columns_container.columnconfigure(1, weight=1, uniform="cols3")
            self.columns_container.columnconfigure(2, weight=1, uniform="cols3")

            self.callbacks['viewer1'].grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.callbacks['viewer2'].grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
            self.callbacks['viewer3'].grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

    def _update_sync_button_style(self):
        """Atualiza a aparência do botão de trava de sincronização (símbolo 🔒 ou 🔓)."""
        if self.callbacks.get('sync_locked', True):
            self.btn_sync.config(
                text="🔒",
                bg="#16a34a",
                fg="white",
                activebackground="#15803d",
                activeforeground="white"
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="Sincronização ativada (🔒): pan e zoom aplicados em uma imagem moverão as outras."
                )
        else:
            self.btn_sync.config(
                text="🔓",
                bg="#4b5563",
                fg="#f4f4f5",
                activebackground="#374151",
                activeforeground="white"
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="Sincronização destravada (🔓): ajuste cada imagem individualmente para alinhamento."
                )

    def update_sync_button(self, sync_locked):
        """Atualiza o estado do botão de sincronização."""
        self.callbacks['sync_locked'] = sync_locked
        self._update_sync_button_style()

    def update_third_column_button(self, visible):
        """Atualiza o botão da terceira coluna."""
        self.third_column_visible = visible
        if visible:
            self.btn_toggle_3rd.config(
                text="❌  3ª Imagem (ocultar)",
                bg="#3f3f46",
                activebackground="#52525b"
            )
        else:
            self.btn_toggle_3rd.config(
                text="➕ 3ª Imagem",
                bg="#3f3f46",
                activebackground="#52525b"
            )

    def set_status(self, text):
        """Atualiza o texto da barra de status."""
        if hasattr(self, "lbl_status"):
            self.lbl_status.config(text=text)