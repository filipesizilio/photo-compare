"""
================================================================================
Projeto: Photo Compare
Descrição: Ferramenta desktop para comparação visual simultânea de imagens lado a
           lado (2 ou 3 colunas) com suporte a pan e zoom sincronizados ou
           independentes, arrastar e soltar (Drag & Drop) nativo do Windows e
           renderização de alto desempenho via Pillow.
Criado por: Filipe Sizilio
Data de criação: 01/09/2023

Arquivo: photocompare.py
Função do Script:
    Ponto de entrada principal da aplicação. Compose os módulos especializados
    (config, UI, image_loader, viewer_coordinator, toolbar_actions) na classe
    principal PhotoCompareApp.
================================================================================
"""

import json
import os
import sys
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
try:
    import tkinterdnd2 as tkdnd
    TKDND_AVAILABLE = True
except ImportError:
    tkdnd = tk
    TKDND_AVAILABLE = False

from image_viewer import ImageViewer
from app_config import AppConfig
from app_ui import AppUI
from image_loader import ImageLoader
from viewer_coordinator import ViewerCoordinator
from toolbar_actions import ToolbarActions


class PhotoCompareApp(tkdnd.Tk if TKDND_AVAILABLE else tk.Tk):
    """Janela principal da aplicação Photo Compare."""

    def __init__(self):
        super().__init__()

        self.title("Photo Compare - Comparador de Imagens")
        self.minsize(800, 500)
        self.configure(bg="#0f0f11")

        # Callbacks compartilhados entre módulos
        self.callbacks = {
            'toggle_sync': self.toggle_sync,
            'toggle_third_column': self.toggle_third_column,
            'fit_all_to_window': self.fit_all_to_window,
            'reset_all_100': self.reset_all_100,
            'align_to_first_panel': self.align_to_first_panel,
            'show_exif_comparison': self.show_exif_comparison,
            'open_github': self.open_github,
            'open_images_dialog': self.open_images_dialog,
            'set_status': self.set_status,
            'show_warning': self.show_warning,
            'sync_locked': True,  # Estado de sincronização armazenado diretamente
        }

        # Inicializa módulos de configuração e UI primeiro (cria columns_container)
        self.app_config = AppConfig(self)
        self.app_ui = AppUI(self, None, None, None, self.callbacks)
        
        # Agora cria os visualizadores com columns_container como parent
        self.viewer1 = ImageViewer(
            self.app_ui.columns_container,
            title="Imagem 1",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self._open_next_empty
        )
        self.viewer2 = ImageViewer(
            self.app_ui.columns_container,
            title="Imagem 2",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self._open_next_empty
        )
        self.viewer3 = ImageViewer(
            self.app_ui.columns_container,
            title="Imagem 3",
            on_pan_callback=self._on_viewer_pan,
            on_zoom_callback=self._on_viewer_zoom,
            on_open_request_callback=self._open_next_empty
        )

        # Dicionário de visualizadores para fácil acesso
        self.viewers = {
            'viewer1': self.viewer1,
            'viewer2': self.viewer2,
            'viewer3': self.viewer3,
        }

        # Atualiza callbacks com referências aos visualizadores
        self.callbacks.update({
            'viewer1': self.viewer1,
            'viewer2': self.viewer2,
            'viewer3': self.viewer3,
        })

        # Agora que os visualizadores existem, organiza as colunas
        self.app_ui._arrange_columns()

        # Inicializa módulos especializados
        self.image_loader = ImageLoader(self, self.viewers, self.callbacks)
        self.viewer_coordinator = ViewerCoordinator(self.viewers, self.callbacks)
        
        self.toolbar_actions = ToolbarActions(self, self.app_ui, self.viewer_coordinator, self.image_loader, self.callbacks)

        # Configuração da janela
        self.app_config.load_and_apply_geometry()
        self.app_config.set_app_icon()

        # Estado da sincronização
        self.sync_locked = True
        self.third_column_visible = False

        # Vincula callbacks dos visualizadores ao coordenador
        self._bind_viewer_callbacks()

        # Atalhos de teclado globais
        self._bind_global_shortcuts()

        # Monitora redimensionamento e fechamento para persistência
        self.bind("<Configure>", self.app_config.on_window_configure)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_viewer_callbacks(self):
        """Vincula os callbacks de pan/zoom dos visualizadores ao coordenador."""
        for viewer in self.viewers.values():
            viewer.on_pan_callback = self.viewer_coordinator.on_viewer_pan
            viewer.on_zoom_callback = self.viewer_coordinator.on_viewer_zoom

    def _bind_global_shortcuts(self):
        """Atalhos de teclado para produtividade."""
        self.bind("<space>", lambda e: self.toggle_sync())
        self.bind("<f>", lambda e: self.fit_all_to_window())
        self.bind("<F>", lambda e: self.fit_all_to_window())
        self.bind("<Control-o>", lambda e: self._open_next_empty())

    def _open_next_empty(self, target_viewer=None):
        """Abre o seletor permitindo escolher até 3 imagens."""
        if target_viewer is None:
            for v in self.viewer_coordinator.get_visible_viewers():
                if not v.pil_image:
                    target_viewer = v
                    break
        self.open_images_dialog(target_viewer=target_viewer)

    def _on_viewer_pan(self, source_viewer, dx, dy):
        """Callback de pan encaminhado para o coordenador."""
        self.viewer_coordinator.on_viewer_pan(source_viewer, dx, dy)

    def _on_viewer_zoom(self, source_viewer, factor, mouse_x, mouse_y):
        """Callback de zoom encaminhado para o coordenador."""
        self.viewer_coordinator.on_viewer_zoom(source_viewer, factor, mouse_x, mouse_y)

    def _on_close(self):
        """Salva a geometria e o estado maximizado da janela antes de fechar."""
        self.app_config.on_close()
        self.destroy()

    def set_status(self, text):
        """Atualiza o texto da barra de status."""
        self.app_ui.set_status(text)

    def show_warning(self, title, message):
        """Exibe um aviso."""
        messagebox.showwarning(title, message)

    def open_github(self):
        """Abre o repositório GitHub no navegador."""
        webbrowser.open("https://github.com/filipesizilio/photo-compare")

    def open_images_dialog(self, target_viewer=None):
        """Abre o seletor de arquivos permitindo seleção de até 3 imagens."""
        self.image_loader.open_images_dialog(target_viewer=target_viewer)

    def toggle_sync(self):
        """Alterna entre modo sincronizado (travado) e independente (destravado)."""
        self.toolbar_actions.toggle_sync()
        self.sync_locked = self.viewer_coordinator.sync_locked
        # Atualiza o estado no dicionário de callbacks
        self.callbacks['sync_locked'] = self.sync_locked

    def get_visible_viewers(self):
        """Retorna os visualizadores atualmente visíveis."""
        return self.viewer_coordinator.get_visible_viewers()

    def load_images_batch(self, paths, target_viewer=None):
        """Compatibilidade pública para o carregador de imagens."""
        self.image_loader.load_images_batch(paths, target_viewer=target_viewer)

    def toggle_third_column(self):
        """Alterna a exibição da terceira coluna."""
        self.toolbar_actions.toggle_third_column()
        self.third_column_visible = self.viewer_coordinator.third_column_visible

    def fit_all_to_window(self):
        """Ajusta todas as imagens abertas ao tamanho de seus respectivos canvas."""
        self.toolbar_actions.fit_all_to_window()

    def reset_all_100(self):
        """Redefine o zoom de todas as imagens abertas para 100% (1:1)."""
        self.toolbar_actions.reset_all_100()

    def align_to_first_panel(self):
        """Alinha a escala e a posição das outras colunas com base no Painel 1."""
        self.toolbar_actions.align_to_first_panel()

    def show_exif_comparison(self):
        """Abre o popup de comparação de dados EXIF das imagens carregadas."""
        self.toolbar_actions.show_exif_comparison()


def main():
    """Função de entrada para iniciar o Photo Compare."""
    app = PhotoCompareApp()
    app.mainloop()


if __name__ == "__main__":
    main()