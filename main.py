"""
Photo Compare - Ferramenta de comparação de imagens lado a lado com Tkinter e Pillow.
Permite comparar 2 ou 3 imagens simultaneamente com pan e zoom sincronizados.
"""

import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from image_viewer import ImageViewer
from drag_drop import is_image_file, enable_drag_drop


def resource_path(relative_path):
    """Retorna o caminho absoluto para recursos, compatível com execução normal e empacotada (.exe)."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


class PhotoCompareApp(tk.Tk):
    """Janela principal da aplicação Photo Compare."""

    def __init__(self):
        super().__init__()

        self.title("Photo Compare - Comparador de Imagens")
        self.geometry("1280x760")
        self.minsize(800, 500)
        self.configure(bg="#0f0f11")

        self._set_app_icon()

        # Estado da sincronização
        self.sync_locked = True
        self.third_column_visible = False

        self._init_style()
        self._build_ui()
        self._bind_global_shortcuts()

    def _init_style(self):
        """Configurações visuais do ttk para combinar com o tema escuro."""
        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass

    def _set_app_icon(self):
        """Define o ícone da aplicação na barra de título e barra de tarefas."""
        icon_ico = resource_path(os.path.join("assets", "icon.ico"))
        icon_png = resource_path(os.path.join("assets", "icon.png"))
        if os.path.exists(icon_ico):
            try:
                self.iconbitmap(icon_ico)
            except Exception:
                pass
        if os.path.exists(icon_png):
            try:
                self._app_icon_img = tk.PhotoImage(file=icon_png)
                self.iconphoto(True, self._app_icon_img)
            except Exception:
                pass

    def _build_ui(self):
        # 1. Barra de ferramentas superior
        self.toolbar = tk.Frame(self, bg="#18181b", height=50, padx=12, pady=6)
        self.toolbar.pack(fill=tk.X, side=tk.TOP)
        self.toolbar.pack_propagate(False)

        # Logotipo / Nome do App
        lbl_brand = tk.Label(
            self.toolbar,
            text="🔍 Photo Compare",
            font=("Segoe UI", 12, "bold"),
            fg="#f4f4f5",
            bg="#18181b"
        )
        lbl_brand.pack(side=tk.LEFT, padx=(0, 16))

        # Divisor visual
        sep1 = tk.Frame(self.toolbar, bg="#27272a", width=1, height=28)
        sep1.pack(side=tk.LEFT, padx=(0, 16), fill=tk.Y, pady=4)

        # Botão de Trava de Sincronização (Destaque Principal)
        self.btn_sync = tk.Button(
            self.toolbar,
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.toggle_sync
        )
        self.btn_sync.pack(side=tk.LEFT, padx=(0, 10))

        # Botão para alternar 3ª Coluna
        self.btn_toggle_3rd = tk.Button(
            self.toolbar,
            text="➕ Adicionar 3ª Imagem",
            font=("Segoe UI", 9, "bold"),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.toggle_third_column
        )
        self.btn_toggle_3rd.pack(side=tk.LEFT, padx=(0, 10))

        # Divisor visual
        sep2 = tk.Frame(self.toolbar, bg="#27272a", width=1, height=28)
        sep2.pack(side=tk.LEFT, padx=(0, 16), fill=tk.Y, pady=4)

        # Botão Ajustar Todas
        self.btn_fit_all = tk.Button(
            self.toolbar,
            text="⤢ Ajustar Todas",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.fit_all_to_window
        )
        self.btn_fit_all.pack(side=tk.LEFT, padx=3)

        # Botão 100% Todas
        self.btn_reset_all = tk.Button(
            self.toolbar,
            text="1:1 (Tamanho Real)",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.reset_all_100
        )
        self.btn_reset_all.pack(side=tk.LEFT, padx=3)

        # Botão Alinhar ao Painel 1
        self.btn_align_panel1 = tk.Button(
            self.toolbar,
            text="🎯 Alinhar ao Painel 1",
            font=("Segoe UI", 9),
            bg="#27272a",
            fg="#e4e4e7",
            activebackground="#3f3f46",
            activeforeground="white",
            relief=tk.FLAT,
            padx=9,
            pady=4,
            cursor="hand2",
            command=self.align_to_first_panel
        )
        self.btn_align_panel1.pack(side=tk.LEFT, padx=3)

        # Dica rápida no lado direito
        lbl_hint = tk.Label(
            self.toolbar,
            text="Atalho: [Espaço] para Travar/Destravar • [F] Ajustar",
            font=("Segoe UI", 9),
            fg="#71717a",
            bg="#18181b"
        )
        lbl_hint.pack(side=tk.RIGHT, padx=4)

        # 2. Barra de status inferior
        self.statusbar = tk.Frame(self, bg="#18181b", height=26, padx=12)
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
            lambda e: webbrowser.open("https://github.com/filipesizilio/photo-compare")
        )
        self.lbl_github.bind("<Enter>", lambda e: self.lbl_github.config(fg="#93c5fd"))
        self.lbl_github.bind("<Leave>", lambda e: self.lbl_github.config(fg="#60a5fa"))

        self._update_sync_button_style()

        # 3. Área central com colunas de comparação
        self.columns_container = tk.Frame(self, bg="#09090b")
        self.columns_container.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.columns_container.rowconfigure(0, weight=1)

        # Instancia os 3 visualizadores com títulos Imagem 1, Imagem 2 e Imagem 3
        self.viewer1 = ImageViewer(
            self.columns_container,
            title="Imagem 1",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self.open_images_dialog
        )
        self.viewer2 = ImageViewer(
            self.columns_container,
            title="Imagem 2",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self.open_images_dialog
        )
        self.viewer3 = ImageViewer(
            self.columns_container,
            title="Imagem 3",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self.open_images_dialog
        )

        # Exibe inicialmente Coluna 1 e Coluna 2 lado a lado
        self._arrange_columns()

        # Habilita suporte a Arraste e Solte (Drag & Drop) nativo na janela
        enable_drag_drop(self, self._on_window_drop)

    def _arrange_columns(self):
        """Organiza as colunas em grid proporcional de acordo com a visibilidade."""
        # Limpa layout anterior
        self.viewer1.grid_forget()
        self.viewer2.grid_forget()
        self.viewer3.grid_forget()

        if not self.third_column_visible:
            self.columns_container.columnconfigure(0, weight=1, uniform="cols")
            self.columns_container.columnconfigure(1, weight=1, uniform="cols")
            self.columns_container.columnconfigure(2, weight=0)

            self.viewer1.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.viewer2.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
        else:
            self.columns_container.columnconfigure(0, weight=1, uniform="cols")
            self.columns_container.columnconfigure(1, weight=1, uniform="cols")
            self.columns_container.columnconfigure(2, weight=1, uniform="cols")

            self.viewer1.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
            self.viewer2.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)
            self.viewer3.grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

    def _bind_global_shortcuts(self):
        """Atalhos de teclado para produtividade."""
        self.bind("<space>", lambda e: self.toggle_sync())
        self.bind("<f>", lambda e: self.fit_all_to_window())
        self.bind("<F>", lambda e: self.fit_all_to_window())
        self.bind("<Control-o>", lambda e: self._open_next_empty())

    def _open_next_empty(self):
        """Abre o seletor permitindo escolher até 3 imagens."""
        target = None
        for v in self.get_visible_viewers():
            if not v.pil_image:
                target = v
                break
        self.open_images_dialog(target_viewer=target)

    def _get_viewer_for_widget(self, widget):
        """Identifica a qual ImageViewer o widget pertence (por hierarquia de parentesco)."""
        curr = widget
        while curr is not None:
            if curr is self.viewer1:
                return self.viewer1
            if curr is self.viewer2:
                return self.viewer2
            if self.third_column_visible and curr is self.viewer3:
                return self.viewer3
            curr = getattr(curr, "master", None)
        return None

    def _on_window_drop(self, file_paths, drop_x, drop_y):
        """Callback acionado quando arquivos são arrastados e soltos na janela do programa."""
        if not file_paths:
            return

        target_viewer = None
        try:
            ptr_x = self.winfo_pointerx()
            ptr_y = self.winfo_pointery()
            hovered_widget = self.winfo_containing(ptr_x, ptr_y)
            target_viewer = self._get_viewer_for_widget(hovered_widget)
        except Exception:
            pass

        self.load_images_batch(file_paths, target_viewer=target_viewer)

    def open_images_dialog(self, target_viewer=None):
        """Abre o seletor de arquivos permitindo seleção de até 3 imagens."""
        file_types = [
            (
                "Arquivos de Imagem",
                "*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif *.ico *.gif",
            ),
            ("JPEG (*.jpg, *.jpeg)", "*.jpg *.jpeg"),
            ("PNG (*.png)", "*.png"),
            ("WEBP (*.webp)", "*.webp"),
            ("BMP (*.bmp)", "*.bmp"),
            ("TIFF (*.tiff, *.tif)", "*.tiff *.tif"),
            ("Todos os Arquivos", "*.*"),
        ]
        title = "Selecionar Imagens (até 3)"
        if target_viewer:
            title += f" - {target_viewer.title}"

        chosen_paths = filedialog.askopenfilenames(
            title=title,
            filetypes=file_types
        )
        if chosen_paths:
            self.load_images_batch(list(chosen_paths), target_viewer=target_viewer)

    def load_images_batch(self, paths, target_viewer=None):
        """
        Carrega lote de imagens (selecionadas ou arrastadas) aplicando as regras do Photo Compare:
        - 1 imagem: carrega no target_viewer (se clicado) ou na 1ª coluna livre (esquerda para direita).
        - 2 imagens: carrega na Imagem 1 (esquerda) e Imagem 2 (direita).
        - 3 imagens: abre automaticamente a 3ª coluna e carrega em Imagem 1, 2 e 3 da esquerda para a direita.
        - Mais de 3 imagens: carrega as 3 primeiras e notifica o usuário.
        """
        valid_paths = [p for p in paths if os.path.isfile(p) and is_image_file(p)]
        if not valid_paths:
            if paths:
                messagebox.showwarning(
                    "Formato não suportado",
                    "Nenhum arquivo de imagem compatível foi encontrado entre os arquivos selecionados ou soltos."
                )
            return

        total = len(valid_paths)
        if total > 3:
            valid_paths = valid_paths[:3]
            total = 3
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="Aviso: Limite de 3 imagens por vez. Carregando as 3 primeiras."
                )

        if total == 1:
            img_path = valid_paths[0]
            dest_viewer = target_viewer
            if dest_viewer is None:
                for v in self.get_visible_viewers():
                    if not v.pil_image:
                        dest_viewer = v
                        break
                if dest_viewer is None:
                    dest_viewer = self.viewer1

            dest_viewer.load_image(img_path)
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text=f"Imagem carregada em {dest_viewer.title}: {os.path.basename(img_path)}"
                )

        elif total == 2:
            self.viewer1.load_image(valid_paths[0])
            self.viewer2.load_image(valid_paths[1])
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="2 imagens carregadas: Imagem 1 (esquerda) e Imagem 2 (direita)."
                )

        elif total >= 3:
            # Abre automaticamente a 3ª coluna se estiver fechada
            if not self.third_column_visible:
                self.toggle_third_column()

            self.viewer1.load_image(valid_paths[0])
            self.viewer2.load_image(valid_paths[1])
            self.viewer3.load_image(valid_paths[2])
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="3 imagens carregadas sequencialmente e 3ª coluna aberta automaticamente."
                )

    def get_visible_viewers(self):
        """Retorna lista dos visualizadores visíveis no momento."""
        viewers = [self.viewer1, self.viewer2]
        if self.third_column_visible:
            viewers.append(self.viewer3)
        return viewers

    def toggle_sync(self):
        """Alterna entre modo sincronizado (travado) e independente (destravado)."""
        self.sync_locked = not self.sync_locked
        self._update_sync_button_style()

    def _update_sync_button_style(self):
        """Atualiza a aparência do botão de trava de sincronização."""
        if self.sync_locked:
            self.btn_sync.config(
                text="🔒 Sincronização: TRAVADA (Ativa)",
                bg="#16a34a",
                fg="white",
                activebackground="#15803d",
                activeforeground="white"
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="Sincronização ativada: pan e zoom aplicados em uma imagem moverão as outras."
                )
        else:
            self.btn_sync.config(
                text="🔓 Sincronização: DESTRAVADA",
                bg="#4b5563",
                fg="#f4f4f5",
                activebackground="#374151",
                activeforeground="white"
            )
            if hasattr(self, "lbl_status"):
                self.lbl_status.config(
                    text="Sincronização destravada: ajuste cada imagem individualmente para alinhamento."
                )

    def toggle_third_column(self):
        """Alterna a exibição da terceira coluna."""
        self.third_column_visible = not self.third_column_visible
        if self.third_column_visible:
            self.btn_toggle_3rd.config(
                text="➖ Ocultar 3ª Coluna",
                bg="#7f1d1d",
                activebackground="#991b1b"
            )
            self._arrange_columns()
            # Se a sincronização estiver ativa e já houver imagem no painel 1, tenta ajustar
            if self.sync_locked and self.viewer1.pil_image and self.viewer3.pil_image:
                self.align_to_first_panel()
        else:
            self.btn_toggle_3rd.config(
                text="➕ Adicionar 3ª Imagem",
                bg="#3f3f46",
                activebackground="#52525b"
            )
            self._arrange_columns()

    # Callbacks de sincronização acionados pelos visualizadores
    def _on_viewer_pan(self, source_viewer, dx, dy):
        """Espelha o deslocamento de pan para as outras colunas se travado."""
        if not self.sync_locked:
            return

        for viewer in self.get_visible_viewers():
            if viewer is not source_viewer and viewer.pil_image:
                viewer.pan(dx, dy, trigger_callback=False)

    def _on_viewer_zoom(self, source_viewer, factor, mouse_x, mouse_y):
        """Espelha o zoom para as outras colunas proporcionalmente ao centro/cursor."""
        if not self.sync_locked:
            return

        src_w = max(1, source_viewer.canvas.winfo_width())
        src_h = max(1, source_viewer.canvas.winfo_height())
        rel_x = mouse_x / src_w
        rel_y = mouse_y / src_h

        for viewer in self.get_visible_viewers():
            if viewer is not source_viewer and viewer.pil_image:
                tgt_w = max(1, viewer.canvas.winfo_width())
                tgt_h = max(1, viewer.canvas.winfo_height())
                target_x = rel_x * tgt_w
                target_y = rel_y * tgt_h
                viewer.zoom(factor, target_x, target_y, trigger_callback=False)

    def fit_all_to_window(self):
        """Ajusta todas as imagens abertas ao tamanho de seus respectivos canvas."""
        for v in self.get_visible_viewers():
            v.fit_to_window()
        self.lbl_status.config(text="Todas as imagens foram ajustadas à tela.")

    def reset_all_100(self):
        """Redefine o zoom de todas as imagens abertas para 100% (1:1)."""
        for v in self.get_visible_viewers():
            v.reset_100()
        self.lbl_status.config(text="Todas as imagens foram definidas para 100% (1:1).")

    def align_to_first_panel(self):
        """
        Alinha a escala e a posição das outras colunas com base no Painel 1.
        Muito útil para quando imagens de resoluções semelhantes precisam de alinhamento perfeito imediato.
        """
        ref = self.viewer1
        if not ref.pil_image:
            messagebox.showinfo(
                "Aviso",
                "Abra uma imagem no Painel 1 primeiro para usá-lo como referência de alinhamento."
            )
            return

        ref_cw = max(1, ref.canvas.winfo_width())
        ref_ch = max(1, ref.canvas.winfo_height())
        # Centro do viewport atual na imagem de referência (coordenadas da imagem)
        center_img_x = (ref_cw / 2.0 - ref.offset_x) / ref.scale
        center_img_y = (ref_ch / 2.0 - ref.offset_y) / ref.scale

        for viewer in self.get_visible_viewers():
            if viewer is not ref and viewer.pil_image:
                tgt_cw = max(1, viewer.canvas.winfo_width())
                tgt_ch = max(1, viewer.canvas.winfo_height())

                # Adota a mesma escala do painel de referência
                viewer.scale = ref.scale
                viewer.offset_x = tgt_cw / 2.0 - center_img_x * viewer.scale
                viewer.offset_y = tgt_ch / 2.0 - center_img_y * viewer.scale
                viewer.render()

        self.lbl_status.config(text="Todos os painéis foram alinhados com base no Painel 1.")


def main():
    app = PhotoCompareApp()
    app.mainloop()


if __name__ == "__main__":
    main()
