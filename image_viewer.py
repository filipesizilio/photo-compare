"""
================================================================================
Projeto: Photo Compare
Descrição: Ferramenta desktop para comparação visual simultânea de imagens lado a
           lado (2 ou 3 colunas) com suporte a pan e zoom sincronizados ou
           independentes, arrastar e soltar (Drag & Drop) nativo do Windows e
           renderização de alto desempenho via Pillow.
Criado por: Filipe Sizilio
Data de criação: 01/09/2023
Versão: 1.0.2


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
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk, ImageDraw, ImageFont
from image_renderer import ViewerRenderer
from image_viewer_io import ViewerImageIO
from image_viewer_interaction import ViewerInteraction
from app_config import (
    CORNER_RADIUS,
    COLOR_VIEWER_BG,
    COLOR_VIEWER_HEADER,
    COLOR_VIEWER_TITLE,
    COLOR_PRIMARY,
    COLOR_PRIMARY_HOVER,
    COLOR_PRIMARY_TEXT,
    COLOR_BTN_ACTION_FG,
    COLOR_BTN_ACTION_HOVER,
    COLOR_BTN_ACTION_TEXT,
    COLOR_BTN_DANGER_FG,
    COLOR_BTN_DANGER_HOVER,
    COLOR_BTN_DANGER_TEXT,
    COLOR_CANVAS_BG,
    COLOR_CANVAS_BORDER,
    COLOR_SEPARATOR,
    get_mode_color,
    get_accent_color_for_title,
)


class ImageViewer(ctk.CTkFrame):
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
        title="Imagem A",
        on_pan_callback=None,
        on_zoom_callback=None,
        on_open_request_callback=None,
        accent_color=None,
        **kwargs
    ):
        # Remove chaves legadas de bg se passadas via kwargs
        kwargs.pop("bg", None)
        self.title = title
        self.accent_color = accent_color or get_accent_color_for_title(title)
        super().__init__(
            parent,
            fg_color=COLOR_VIEWER_BG,
            corner_radius=CORNER_RADIUS,
            border_width=4,
            border_color=self.accent_color,
            **kwargs
        )

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

        self.renderer = ViewerRenderer(self)
        self.image_io = ViewerImageIO(self)
        self.interaction = ViewerInteraction(self)

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        # Barra superior do painel
        self.header = ctk.CTkFrame(
            self,
            fg_color=COLOR_VIEWER_HEADER,
            corner_radius=CORNER_RADIUS,
            height=38
        )
        self.header.pack(fill=tk.X, side=tk.TOP, padx=6, pady=(6, 3))
        self.header.pack_propagate(False)

        # Título da coluna (exibe título e nível de zoom com a cor de destaque da imagem)
        self.lbl_title = ctk.CTkLabel(
            self.header,
            text=self.title,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.accent_color
        )
        # Suporte a chamada legada .config(text=...)
        self.lbl_title.config = self.lbl_title.configure
        self.lbl_title.pack(side=tk.LEFT, padx=(10, 8))

        # Botão Abrir - texto "📂", tamanho padronizado
        self.btn_open = ctk.CTkButton(
            self.header,
            text="📂",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_PRIMARY_TEXT,
            width=32,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self.open_file_dialog
        )
        self.btn_open.pack(side=tk.LEFT, padx=2)

        # Botão Ajustar à Tela - texto "⛶", tamanho padronizado
        self.btn_fit = ctk.CTkButton(
            self.header,
            text="⛶",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=14, weight="bold"),
            fg_color=COLOR_BTN_ACTION_FG,
            hover_color=COLOR_BTN_ACTION_HOVER,
            text_color=COLOR_BTN_ACTION_TEXT,
            width=32,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self.fit_to_window
        )
        self.btn_fit.pack(side=tk.LEFT, padx=2)

        # Botão 1:1 - texto "1:1", tamanho padronizado
        self.btn_100 = ctk.CTkButton(
            self.header,
            text="1:1",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_BTN_ACTION_FG,
            hover_color=COLOR_BTN_ACTION_HOVER,
            text_color=COLOR_BTN_ACTION_TEXT,
            width=32,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self.reset_100
        )
        self.btn_100.pack(side=tk.LEFT, padx=2)

        # Botão Girar 90° - texto "↻", tamanho padronizado
        self.btn_rotate = ctk.CTkButton(
            self.header,
            text="↻",
            font=ctk.CTkFont(family="Segoe UI Symbol", size=14, weight="bold"),
            fg_color=COLOR_BTN_ACTION_FG,
            hover_color=COLOR_BTN_ACTION_HOVER,
            text_color=COLOR_BTN_ACTION_TEXT,
            width=32,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self.rotate_90
        )
        self.btn_rotate.pack(side=tk.LEFT, padx=2)

        # Botão Fechar Imagem ("X") no canto superior direito da coluna
        self.btn_close = ctk.CTkButton(
            self.header,
            text="✕",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_BTN_DANGER_FG,
            hover_color=COLOR_BTN_DANGER_HOVER,
            text_color=COLOR_BTN_DANGER_TEXT,
            width=32,
            height=28,
            corner_radius=CORNER_RADIUS,
            command=self.close_image
        )

        # Canvas para exibição da imagem e da legenda sobreposta
        self.canvas = tk.Canvas(
            self,
            bg=get_mode_color(COLOR_CANVAS_BG),
            highlightthickness=0,
            cursor="arrow"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=(3, 6))

        # Atualização dinâmica ao alternar modo claro/escuro
        ctk.AppearanceModeTracker.add(self._on_appearance_mode_change)

    def _on_appearance_mode_change(self, mode=None):
        self.update_appearance_mode()

    def update_appearance_mode(self):
        """Atualiza o canvas e redesenha elementos visuais ao alternar modo claro/escuro."""
        try:
            if not self.winfo_exists():
                return
            self.configure(border_color=self.accent_color)
            self.lbl_title.configure(text_color=self.accent_color)
            self.canvas.configure(
                bg=get_mode_color(COLOR_CANVAS_BG),
            )
            if not self.pil_image:
                self.renderer.draw_empty_state()
            else:
                self.renderer.render()
        except Exception:
            pass

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
        self.image_io.open_file_dialog()

    def load_image(self, file_path):
        """Carrega uma imagem a partir do caminho do arquivo."""
        self.image_io.load_image(file_path)

    def close_image(self):
        """Fecha e descarrega a imagem atual da coluna."""
        self.image_io.close_image()

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

    def rotate_90(self):
        """Gira a imagem 90° no sentido horário, mantendo o centro da visualização."""
        self.interaction.rotate_90()

    def zoom(self, factor, mouse_x, mouse_y, trigger_callback=True):
        """
        Aplica o zoom centrado nas coordenadas (mouse_x, mouse_y).
        Mantém a precisão geométrica e notifica o callback se solicitado.
        """
        self.interaction.zoom(factor, mouse_x, mouse_y, trigger_callback)

    def pan(self, dx, dy, trigger_callback=True):
        """
        Desloca a visualização da imagem em dx e dy pixels.
        Notifica o callback se solicitado.
        """
        self.interaction.pan(dx, dy, trigger_callback)

    def render(self):
        self.renderer.render()

    def _get_image_date(self):
        return self.renderer.get_image_date()

    def _draw_overlay_legend(self, cw, ch):
        self.renderer.draw_overlay_legend(cw, ch)

    def _draw_empty_state(self):
        self.renderer.draw_empty_state()

    def _update_title_zoom(self):
        self.renderer.update_title_zoom()

    # Handlers de Eventos do Mouse
    def _on_button_press(self, event):
        self.interaction.on_button_press(event)

    def _on_mouse_drag(self, event):
        self.interaction.on_mouse_drag(event)

    def _on_button_release(self, event):
        self.interaction.on_button_release(event)

    def _on_mouse_wheel(self, event):
        """Trata scroll no Windows (mouse wheel e trackpad)."""
        self.interaction.on_mouse_wheel(event)

    def _on_mouse_wheel_linux(self, event, direction):
        """Trata scroll no Linux (Button-4 / Button-5)."""
        self.interaction.on_mouse_wheel_linux(event, direction)

    def _on_resize(self, event):
        """Re-renderiza o viewport quando o canvas for redimensionado."""
        self.interaction.on_resize(event)
