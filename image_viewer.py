"""
================================================================================
Projeto: Photo Compare
Descrição: Ferramenta desktop para comparação visual simultânea de imagens lado a
           lado (2 ou 3 colunas) com suporte a pan e zoom sincronizados ou
           independentes, arrastar e soltar (Drag & Drop) nativo do Windows e
           renderização de alto desempenho via Pillow.

Arquivo: image_viewer.py
Função do Script:
    Implementa o widget ImageViewer baseado em tk.Frame e tk.Canvas.
    Gerencia a exibição individual de cada imagem, cálculos matemáticos de zoom
    ancorado na posição do cursor, movimentação (pan), renderização otimizada
    por recorte de viewport visível, sobreposição de legenda com metadados em
    caixa semitransparente (50% preto fumê), exibição do percentual de zoom no
    título da coluna e botões de controle de tamanho padronizado.

Funções Globais:
    - Nenhuma (módulo orientado a objetos centrado na classe ImageViewer).
================================================================================
"""

import math
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont


class ImageViewer(tk.Frame):
    """
    Painel individual de visualização de imagem com suporte a:
    - Zoom ancorado no cursor
    - Pan via arraste do mouse
    - Renderização otimizada com recorte do viewport
    - Sincronização via callbacks
    - Legenda sobreposta em caixa semitransparente (50% preto)
    - Botão 'X' no canto superior direito para fechar a imagem
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
        self.tk_legend = None
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
        self.header = tk.Frame(self, bg="#27272a", height=38, padx=6, pady=3)
        self.header.pack(fill=tk.X, side=tk.TOP)
        self.header.pack_propagate(False)

        # Título da coluna (exibe título e nível de zoom)
        self.lbl_title = tk.Label(
            self.header,
            text=self.title,
            font=("Segoe UI", 10, "bold"),
            fg="#60a5fa",
            bg="#27272a"
        )
        self.lbl_title.pack(side=tk.LEFT, padx=(0, 6))

        # Botão Abrir - texto "📂", tamanho padronizado (width=3)
        self.btn_open = tk.Button(
            self.header,
            text="📂",
            font=("Segoe UI", 9, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief=tk.FLAT,
            width=3,
            pady=1,
            cursor="hand2",
            command=self.open_file_dialog
        )
        self.btn_open.pack(side=tk.LEFT, padx=2)

        # Botão Ajustar à Tela - texto "⤢", tamanho padronizado (width=3)
        self.btn_fit = tk.Button(
            self.header,
            text="⤢",
            font=("Segoe UI", 9, "bold"),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            width=3,
            pady=1,
            cursor="hand2",
            command=self.fit_to_window
        )
        self.btn_fit.pack(side=tk.LEFT, padx=2)

        # Botão 1:1 - texto "1:1", tamanho padronizado (width=3)
        self.btn_100 = tk.Button(
            self.header,
            text="1:1",
            font=("Segoe UI", 9, "bold"),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            width=3,
            pady=1,
            cursor="hand2",
            command=self.reset_100
        )
        self.btn_100.pack(side=tk.LEFT, padx=2)

        # Botão Fechar Imagem ("X") no canto superior direito da coluna, tamanho padronizado (width=3)
        self.btn_close = tk.Button(
            self.header,
            text="✕",
            font=("Segoe UI", 9, "bold"),
            bg="#7f1d1d",
            fg="white",
            activebackground="#991b1b",
            activeforeground="white",
            relief=tk.FLAT,
            width=3,
            pady=1,
            cursor="hand2",
            command=self.close_image
        )

        # Canvas para exibição da imagem e da legenda sobreposta
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
            # Exibe o botão de fechar "X" no canto superior direito da coluna
            self.btn_close.pack(side=tk.RIGHT, padx=4)

            # Ajusta imagem inicialmente à tela
            self.fit_to_window()
        except Exception as err:
            messagebox.showerror(
                "Erro ao abrir imagem",
                f"Não foi possível abrir o arquivo selecionado:\n{err}"
            )

    def close_image(self):
        """Fecha e descarrega a imagem atual da coluna."""
        self.file_path = None
        self.pil_image = None
        self.tk_image = None
        self.tk_legend = None
        self.orig_size = (0, 0)
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0

        self.btn_close.pack_forget()
        self.lbl_title.config(text=self.title)
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
        Renderiza a imagem no Canvas com recorte inteligente do viewport,
        desenha a legenda semitransparente sobre a imagem e atualiza o zoom no título.
        """
        self.canvas.delete("all")

        if not self.pil_image:
            self._draw_empty_state()
            self._update_title_zoom()
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

        if crop_r > crop_l and crop_b > crop_t:
            # Posição e dimensões de destino no canvas
            dst_x = int(round(self.offset_x + crop_l * self.scale))
            dst_y = int(round(self.offset_y + crop_t * self.scale))
            dst_w = int(round((crop_r - crop_l) * self.scale))
            dst_h = int(round((crop_b - crop_t) * self.scale))

            if dst_w > 0 and dst_h > 0:
                crop_box = (
                    int(math.floor(crop_l)),
                    int(math.floor(crop_t)),
                    min(iw, int(math.ceil(crop_r))),
                    min(ih, int(math.ceil(crop_b))),
                )
                try:
                    sub_img = self.pil_image.crop(crop_box)
                    resample_mode = (
                        Image.Resampling.NEAREST
                        if self.scale >= 4.0
                        else Image.Resampling.BILINEAR
                    )
                    resized = sub_img.resize((dst_w, dst_h), resample_mode)
                    self.tk_image = ImageTk.PhotoImage(resized)
                    self.canvas.create_image(dst_x, dst_y, anchor="nw", image=self.tk_image)
                except Exception:
                    pass

        # Desenha a legenda de metadados sobreposta no canto inferior esquerdo
        self._draw_overlay_legend(cw, ch)

        # Atualiza nível de zoom no título da coluna
        self._update_title_zoom()

    def _get_image_date(self):
        """Obtém a data da imagem a partir dos metadados EXIF ou da data de modificação."""
        if not self.file_path or not os.path.exists(self.file_path):
            return ""

        # 1. Tenta extrair DateTimeOriginal ou DateTime do EXIF
        try:
            if self.pil_image:
                exif = getattr(self.pil_image, "getexif", lambda: None)()
                if exif:
                    # 36867: DateTimeOriginal, 306: DateTime
                    exif_date = exif.get(36867) or exif.get(306)
                    if exif_date and isinstance(exif_date, str):
                        parts = exif_date.strip().split(" ")
                        if len(parts) == 2:
                            d_parts = parts[0].split(":")
                            if len(d_parts) == 3:
                                return f"{d_parts[2]}/{d_parts[1]}/{d_parts[0]} {parts[1][:5]}"
        except Exception:
            pass

        # 2. Fallback para data de modificação do arquivo no disco
        try:
            mtime = os.path.getmtime(self.file_path)
            return datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
        except Exception:
            return ""

    def _draw_overlay_legend(self, cw, ch):
        """
        Desenha a caixa de legenda semitransparente (preto fumê 50%)
        no canto inferior esquerdo com caminho do arquivo, resolução, MP e data.
        """
        if not self.file_path or not self.pil_image:
            return

        iw, ih = self.orig_size
        mp = (iw * ih) / 1_000_000.0
        date_str = self._get_image_date()

        line1 = self.file_path
        line2 = f"{mp:.1f} MP ({iw}x{ih})"
        if date_str:
            line2 += f"   •   {date_str}"

        # Carrega fontes com fallback para fonte padrão
        try:
            font_title = ImageFont.truetype("segoeuib.ttf", 11)
            font_sub = ImageFont.truetype("segoeui.ttf", 11)
        except Exception:
            try:
                font_title = ImageFont.truetype("segoeui.ttf", 11)
                font_sub = font_title
            except Exception:
                font_title = ImageFont.load_default()
                font_sub = font_title

        def measure(text, font):
            try:
                bbox = font.getbbox(text)
                return bbox[2] - bbox[0], bbox[3] - bbox[1]
            except Exception:
                return len(text) * 7, 14

        w1, h1 = measure(line1, font_title)
        w2, h2 = measure(line2, font_sub)

        # Ajusta comprimento do caminho se for maior que a largura do canvas
        max_line_w = max(160, cw - 40)
        if w1 > max_line_w:
            while len(line1) > 20 and w1 > max_line_w:
                line1 = "..." + line1[6:]
                w1, h1 = measure(line1, font_title)

        box_w = max(w1, w2) + 20
        box_h = h1 + h2 + 14

        # Fundo preto fumê 50% de opacidade (alfa=128)
        box = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 128))
        draw = ImageDraw.Draw(box)

        # Texto branco com alta legibilidade
        draw.text((10, 4), line1, font=font_title, fill=(255, 255, 255, 255))
        draw.text((10, 6 + h1 + 2), line2, font=font_sub, fill=(235, 235, 235, 225))

        self.tk_legend = ImageTk.PhotoImage(box)
        pos_x = 10
        pos_y = max(10, ch - box_h - 10)

        self.canvas.create_image(
            pos_x, pos_y, anchor="nw", image=self.tk_legend, tags="legend"
        )

        # Permite arrastar sobre a área da legenda.
        # Nota: <MouseWheel> não é permitido em itens de canvas (apenas no canvas em si),
        # mas o scroll já está vinculado corretamente ao canvas em _bind_events().
        self.canvas.tag_bind("legend", "<ButtonPress-1>", self._on_button_press)
        self.canvas.tag_bind("legend", "<B1-Motion>", self._on_mouse_drag)
        self.canvas.tag_bind("legend", "<ButtonRelease-1>", self._on_button_release)
        self.canvas.tag_bind("legend", "<Double-Button-1>", lambda e: self.fit_to_window())

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

    def _update_title_zoom(self):
        """Atualiza o nível de zoom exibido no título da coluna."""
        if not self.pil_image:
            self.lbl_title.config(text=self.title)
        else:
            zoom_pct = int(round(self.scale * 100))
            self.lbl_title.config(text=f"{self.title}  •  {zoom_pct}%")

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
