"""
Componente ImageViewer para visualização e comparação de imagens com suporte a
pan, zoom acelerado por recorte de viewport e callbacks de sincronização.
"""

import math
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class ImageViewer(tk.Frame):
    """
    Painel individual de visualização de imagem com suporte a:
    - Zoom ancorado no cursor
    - Pan via arraste do mouse
    - Renderização otimizada com recorte do viewport
    - Sincronização via callbacks
    """

    MIN_SCALE = 0.01  # 1%
    MAX_SCALE = 50.0  # 5000%
    ZOOM_IN_FACTOR = 1.15
    ZOOM_OUT_FACTOR = 1.0 / 1.15

    def __init__(
        self,
        parent,
        title="Imagem",
        on_pan_callback=None,
        on_zoom_callback=None,
        on_open_request_callback=None,
        **kwargs
    ):
        super().__init__(parent, bg="#18181b", **kwargs)

        self.title = title
        self.on_pan_callback = on_pan_callback
        self.on_zoom_callback = on_zoom_callback
        self.on_open_request_callback = on_open_request_callback

        self.file_path = None
        self.pil_image = None
        self.tk_image = None
        self.orig_size = (0, 0)  # (largura, altura)

        # Estado da visualização
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        # Rastreamento de arraste
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._is_dragging = False

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        # Barra superior do painel
        self.header = tk.Frame(self, bg="#27272a", height=42, padx=8, pady=4)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)

        # Título da coluna
        self.lbl_title = tk.Label(
            self.header,
            text=self.title,
            font=("Segoe UI", 10, "bold"),
            fg="#60a5fa",
            bg="#27272a"
        )
        self.lbl_title.pack(side=tk.LEFT, padx=(0, 8))

        # Botão Abrir
        self.btn_open = tk.Button(
            self.header,
            text="📂 Abrir Imagem",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self.open_file_dialog
        )
        self.btn_open.pack(side=tk.LEFT, padx=4)

        # Botão Ajustar à Tela
        self.btn_fit = tk.Button(
            self.header,
            text="⤢ Ajustar",
            font=("Segoe UI", 9),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.fit_to_window
        )
        self.btn_fit.pack(side=tk.LEFT, padx=3)

        # Botão 100%
        self.btn_100 = tk.Button(
            self.header,
            text="1:1",
            font=("Segoe UI", 9),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.reset_100
        )
        self.btn_100.pack(side=tk.LEFT, padx=3)

        # Botão Fechar Imagem (oculto quando vazio)
        self.btn_close = tk.Button(
            self.header,
            text="✕ Limpar",
            font=("Segoe UI", 9),
            bg="#dc2626",
            fg="white",
            activebackground="#b91c1c",
            activeforeground="white",
            relief=tk.FLAT,
            padx=6,
            pady=2,
            cursor="hand2",
            command=self.close_image
        )

        # Rótulo de informações (nome do arquivo, resolução, zoom)
        self.lbl_info = tk.Label(
            self.header,
            text="Nenhuma imagem carregada",
            font=("Segoe UI", 9),
            fg="#a1a1aa",
            bg="#27272a",
            anchor="e"
        )
        self.lbl_info.pack(side=tk.RIGHT, padx=(4, 0))

        # Canvas para exibição da imagem
        self.canvas = tk.Canvas(
            self,
            bg="#18181b",
            highlightthickness=1,
            highlightbackground="#27272a",
            cursor="arrow"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_events(self):
        # Arraste / Pan
        self.canvas.bind("<ButtonPress-1>", self._on_button_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_button_release)

        # Zoom com roda do mouse (Windows / Linux)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._on_mouse_wheel_linux(e, 1))
        self.canvas.bind("<Button-5>", lambda e: self._on_mouse_wheel_linux(e, -1))

        # Duplo clique para ajustar
        self.canvas.bind("<Double-Button-1>", lambda e: self.fit_to_window())

        # Redimensionamento do canvas
        self.canvas.bind("<Configure>", self._on_resize)

    def open_file_dialog(self):
        """Abre o seletor de arquivos do sistema para carregar imagens."""
        if self.on_open_request_callback:
            self.on_open_request_callback(self)
            return

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
        chosen_paths = filedialog.askopenfilenames(
            title=f"Selecionar Imagem - {self.title}",
            filetypes=file_types
        )
        if chosen_paths:
            self.load_image(chosen_paths[0])

    def load_image(self, file_path):
        """Carrega uma imagem a partir do caminho do arquivo."""
        try:
            img = Image.open(file_path)
            # Converte formatos especiais e aplica fundo neutro para imagens com transparência
            if img.mode == "RGBA":
                bg = Image.new("RGBA", img.size, (24, 24, 27, 255))
                img = Image.alpha_composite(bg, img).convert("RGB")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            self.file_path = file_path
            self.pil_image = img
            self.orig_size = img.size

            self.canvas.config(cursor="fleur")
            self.btn_close.pack(side=tk.LEFT, padx=3)

            # Ajusta imagem inicialmente à tela
            self.fit_to_window()
        except Exception as err:
            messagebox.showerror(
                "Erro ao abrir imagem",
                f"Não foi possível abrir o arquivo selecionado:\n{err}"
            )

    def close_image(self):
        """Fecha e descarrega a imagem atual."""
        self.file_path = None
        self.pil_image = None
        self.tk_image = None
        self.orig_size = (0, 0)
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.btn_close.pack_forget()
        self.canvas.config(cursor="arrow")
        self.render()

    def fit_to_window(self):
        """Ajusta a imagem para caber inteiramente dentro do canvas."""
        if not self.pil_image:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw <= 10 or ch <= 10:
            self.after(50, self.fit_to_window)
            return

        iw, ih = self.orig_size
        padding = 0.96
        scale_w = (cw * padding) / iw
        scale_h = (ch * padding) / ih
        self.scale = min(scale_w, scale_h)

        self.offset_x = (cw - iw * self.scale) / 2.0
        self.offset_y = (ch - ih * self.scale) / 2.0

        self.render()

    def reset_100(self):
        """Redefine o zoom para 100% (1:1), centralizando a imagem."""
        if not self.pil_image:
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        iw, ih = self.orig_size

        self.scale = 1.0
        self.offset_x = (cw - iw) / 2.0
        self.offset_y = (ch - ih) / 2.0

        self.render()

    def zoom(self, factor, mouse_x, mouse_y, trigger_callback=True):
        """
        Aplica o zoom centrado nas coordenadas (mouse_x, mouse_y).
        Mantém a precisão geométrica e notifica o callback se solicitado.
        """
        if not self.pil_image:
            return

        new_scale = max(self.MIN_SCALE, min(self.MAX_SCALE, self.scale * factor))
        if abs(new_scale - self.scale) < 1e-6:
            return

        actual_factor = new_scale / self.scale

        # Atualiza deslocamento para manter o ponto do mouse fixo na imagem
        self.offset_x = mouse_x - (mouse_x - self.offset_x) * actual_factor
        self.offset_y = mouse_y - (mouse_y - self.offset_y) * actual_factor
        self.scale = new_scale

        self.render()

        if trigger_callback and self.on_zoom_callback:
            self.on_zoom_callback(self, factor, mouse_x, mouse_y)

    def pan(self, dx, dy, trigger_callback=True):
        """
        Desloca a visualização da imagem em dx e dy pixels.
        Notifica o callback se solicitado.
        """
        if not self.pil_image:
            return

        self.offset_x += dx
        self.offset_y += dy

        self.render()

        if trigger_callback and self.on_pan_callback:
            self.on_pan_callback(self, dx, dy)

    def render(self):
        """
        Renderiza a imagem no Canvas com recorte inteligente do viewport.
        Garante alta taxa de quadros (60 FPS) mesmo para imagens de 50MP+.
        """
        self.canvas.delete("all")

        if not self.pil_image:
            self._draw_empty_state()
            self._update_info_label()
            return

        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw <= 1 or ch <= 1:
            return

        iw, ih = self.orig_size

        # Converte as coordenadas do retângulo visível do canvas para o espaço da imagem original
        left = -self.offset_x / self.scale
        top = -self.offset_y / self.scale
        right = (cw - self.offset_x) / self.scale
        bottom = (ch - self.offset_y) / self.scale

        # Limita ao retângulo da imagem real
        crop_l = max(0.0, left)
        crop_t = max(0.0, top)
        crop_r = min(float(iw), right)
        crop_b = min(float(ih), bottom)

        if crop_r <= crop_l or crop_b <= crop_t:
            # Imagem fora da área visível
            self._update_info_label()
            return

        # Posição e dimensões de destino no canvas
        dst_x = int(round(self.offset_x + crop_l * self.scale))
        dst_y = int(round(self.offset_y + crop_t * self.scale))
        dst_w = int(round((crop_r - crop_l) * self.scale))
        dst_h = int(round((crop_b - crop_t) * self.scale))

        if dst_w <= 0 or dst_h <= 0:
            self._update_info_label()
            return

        # Caixa de corte inteira para a Pillow
        crop_box = (
            int(math.floor(crop_l)),
            int(math.floor(crop_t)),
            min(iw, int(math.ceil(crop_r))),
            min(ih, int(math.ceil(crop_b))),
        )

        try:
            sub_img = self.pil_image.crop(crop_box)

            # Quando ampliado além de 4x (400%), usamos NEAREST para permitir visualização de pixels
            # Para zooms normais, usamos BILINEAR para máxima suavidade e velocidade
            resample_mode = (
                Image.Resampling.NEAREST
                if self.scale >= 4.0
                else Image.Resampling.BILINEAR
            )
            resized = sub_img.resize((dst_w, dst_h), resample_mode)

            self.tk_image = ImageTk.PhotoImage(resized)
            self.canvas.create_image(dst_x, dst_y, anchor="nw", image=self.tk_image)
        except Exception as e:
            # Em caso de falha de renderização momentânea (ex: redimensionamento extremo)
            pass

        self._update_info_label()

    def _draw_empty_state(self):
        """Desenha a mensagem de instrução quando nenhuma imagem está carregada."""
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1:
            cw = 400
        if ch <= 1:
            ch = 400

        cx, cy = cw // 2, ch // 2

        # Borda pontilhada indicativa
        pad = 20
        self.canvas.create_rectangle(
            pad, pad, cw - pad, ch - pad,
            outline="#3f3f46",
            dash=(4, 4),
            width=1,
            tags="empty"
        )

        self.canvas.create_text(
            cx,
            cy - 20,
            text="📂 Clique para abrir ou arraste arquivos aqui",
            font=("Segoe UI", 12, "bold"),
            fill="#71717a",
            tags="empty"
        )
        self.canvas.create_text(
            cx,
            cy + 16,
            text="Selecione até 3 fotos ou solte do Windows Explorer\nArraste com o mouse para mover • Roda para zoom",
            font=("Segoe UI", 9),
            fill="#52525b",
            justify=tk.CENTER,
            tags="empty"
        )

    def _update_info_label(self):
        """Atualiza o texto de status com nome do arquivo, dimensões e % de zoom."""
        if not self.pil_image:
            self.lbl_info.config(text="Nenhuma imagem")
            return

        filename = os.path.basename(self.file_path) if self.file_path else "Imagem"
        if len(filename) > 24:
            filename = filename[:21] + "..."

        iw, ih = self.orig_size
        zoom_pct = int(round(self.scale * 100))
        self.lbl_info.config(
            text=f"{filename}  |  {iw}x{ih} px  |  {zoom_pct}%"
        )

    # Handlers de Eventos do Mouse
    def _on_button_press(self, event):
        if not self.pil_image:
            self.open_file_dialog()
            return

        self._is_dragging = True
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_mouse_drag(self, event):
        if not self._is_dragging or not self.pil_image:
            return

        dx = event.x - self._drag_start_x
        dy = event.y - self._drag_start_y
        self._drag_start_x = event.x
        self._drag_start_y = event.y

        self.pan(dx, dy, trigger_callback=True)

    def _on_button_release(self, event):
        self._is_dragging = False

    def _on_mouse_wheel(self, event):
        """Trata scroll no Windows (mouse wheel e trackpad)."""
        if not self.pil_image or event.delta == 0:
            return

        steps = event.delta / 120.0
        # Limita o passo máximo por evento para estabilidade
        steps = max(-3.0, min(3.0, steps))
        factor = self.ZOOM_IN_FACTOR ** steps
        self.zoom(factor, event.x, event.y, trigger_callback=True)

    def _on_mouse_wheel_linux(self, event, direction):
        """Trata scroll no Linux (Button-4 / Button-5)."""
        if not self.pil_image:
            return

        factor = self.ZOOM_IN_FACTOR if direction > 0 else self.ZOOM_OUT_FACTOR
        self.zoom(factor, event.x, event.y, trigger_callback=True)

    def _on_resize(self, event):
        """Re-renderiza o viewport quando o canvas for redimensionado."""
        self.render()
