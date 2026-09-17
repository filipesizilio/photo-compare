"""
================================================================================
Módulo: image_loader.py
Descrição: Lógica de carregamento de imagens (carregamento em lote, drag & drop,
           diálogos de arquivo).
================================================================================
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox
from drag_drop import is_image_file, enable_drag_drop


class ImageLoader:
    """Gerencia o carregamento de imagens na aplicação."""

    def __init__(self, root, viewers, callbacks):
        self.root = root
        self.viewers = viewers  # dict com viewer1, viewer2, viewer3
        self.callbacks = callbacks
        self.third_column_visible = False

        # Habilita suporte a Arraste e Solte (Drag & Drop) nativo na janela
        enable_drag_drop(self.root, self._on_window_drop)

    def get_visible_viewers(self):
        """Retorna lista dos visualizadores visíveis no momento."""
        viewers = [self.viewers['viewer1'], self.viewers['viewer2']]
        if self.third_column_visible:
            viewers.append(self.viewers['viewer3'])
        return viewers

    def _get_viewer_for_widget(self, widget):
        """Identifica a qual ImageViewer o widget pertence (por hierarquia de parentesco)."""
        curr = widget
        while curr is not None:
            if curr is self.viewers['viewer1']:
                return self.viewers['viewer1']
            if curr is self.viewers['viewer2']:
                return self.viewers['viewer2']
            if self.third_column_visible and curr is self.viewers['viewer3']:
                return self.viewers['viewer3']
            curr = getattr(curr, "master", None)
        return None

    def _on_window_drop(self, file_paths, drop_x, drop_y):
        """Callback acionado quando arquivos são arrastados e soltos na janela do programa."""
        if not file_paths:
            return

        target_viewer = None
        try:
            ptr_x = self.root.winfo_pointerx()
            ptr_y = self.root.winfo_pointery()
            hovered_widget = self.root.winfo_containing(ptr_x, ptr_y)
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
        - 2 imagens: carrega na Imagem A (esquerda) e Imagem B (direita).
        - 3 imagens: abre automaticamente a 3ª coluna e carrega em Imagem A, B e C da esquerda para a direita.
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
            self.callbacks['set_status']("Aviso: Limite de 3 imagens por vez. Carregando as 3 primeiras.")

        if total == 1:
            img_path = valid_paths[0]
            dest_viewer = target_viewer
            if dest_viewer is None:
                for v in self.get_visible_viewers():
                    if not v.pil_image:
                        dest_viewer = v
                        break
                if dest_viewer is None:
                    dest_viewer = self.viewers['viewer1']

            dest_viewer.load_image(img_path)
            self.callbacks['set_status'](f"Imagem carregada em {dest_viewer.title}: {os.path.basename(img_path)}")

        elif total == 2:
            self.viewers['viewer1'].load_image(valid_paths[0])
            self.viewers['viewer2'].load_image(valid_paths[1])
            self.callbacks['set_status']("2 imagens carregadas: Imagem A (esquerda) e Imagem B (direita).")

        elif total >= 3:
            # Abre automaticamente a 3ª coluna se estiver fechada
            if not self.third_column_visible:
                self.callbacks['toggle_third_column']()

            self.viewers['viewer1'].load_image(valid_paths[0])
            self.viewers['viewer2'].load_image(valid_paths[1])
            self.viewers['viewer3'].load_image(valid_paths[2])
            self.callbacks['set_status']("3 imagens carregadas sequencialmente e 3ª coluna aberta automaticamente.")

    def set_third_column_visible(self, visible):
        """Atualiza o estado de visibilidade da terceira coluna."""
        self.third_column_visible = visible