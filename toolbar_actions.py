"""
================================================================================
Módulo: toolbar_actions.py
Descrição: Ações da barra de ferramentas (alternar sincronização, terceira coluna,
           comparação EXIF).
================================================================================
"""

import tkinter as tk
from tkinter import messagebox
import webbrowser
from exif_tools import show_exif_comparison_popup


class ToolbarActions:
    """Gerencia as ações da barra de ferramentas."""

    def __init__(self, root, ui, viewer_coordinator, image_loader, callbacks):
        self.root = root
        self.ui = ui
        self.viewer_coordinator = viewer_coordinator
        self.image_loader = image_loader
        self.callbacks = callbacks

    def toggle_sync(self):
        """Alterna entre modo sincronizado (travado) e independente (destravado)."""
        self.viewer_coordinator.set_sync_locked(not self.viewer_coordinator.sync_locked)
        self.ui.update_sync_button(self.viewer_coordinator.sync_locked)

    def toggle_third_column(self):
        """Alterna a exibição da terceira coluna."""
        self.viewer_coordinator.set_third_column_visible(not self.viewer_coordinator.third_column_visible)
        self.image_loader.set_third_column_visible(self.viewer_coordinator.third_column_visible)
        
        if self.viewer_coordinator.third_column_visible:
            self.ui.update_third_column_button(True)
            self.ui._arrange_columns()
            if self.viewer_coordinator.sync_locked and self.callbacks['viewer1'].pil_image and self.callbacks['viewer3'].pil_image:
                self.viewer_coordinator.align_to_first_panel()
        else:
            self.ui.update_third_column_button(False)
            self.ui._arrange_columns()

    def show_exif_comparison(self):
        """Abre o popup de comparação de dados EXIF das imagens carregadas."""
        viewers = self.viewer_coordinator.get_visible_viewers()
        show_exif_comparison_popup(self.root, viewers)

    def open_github(self):
        """Abre o repositório GitHub no navegador."""
        webbrowser.open("https://github.com/filipesizilio/photo-compare")

    def fit_all_to_window(self):
        """Ajusta todas as imagens abertas ao tamanho de seus respectivos canvas."""
        self.viewer_coordinator.fit_all_to_window()

    def reset_all_100(self):
        """Redefine o zoom de todas as imagens abertas para 100% (1:1)."""
        self.viewer_coordinator.reset_all_100()

    def align_to_first_panel(self):
        """Alinha a escala e a posição das outras colunas com base no Painel 1."""
        self.viewer_coordinator.align_to_first_panel()