"""Entrada e saída de imagens para o widget ImageViewer."""

import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image


class ViewerImageIO:
    """Gerencia diálogo, carregamento e fechamento da imagem de um viewer."""

    def __init__(self, viewer):
        self.viewer = viewer

    def open_file_dialog(self):
        viewer = self.viewer
        if viewer.on_open_request_callback:
            viewer.on_open_request_callback(viewer)
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
            title=f"Selecionar Imagem - {viewer.title}",
            filetypes=file_types,
        )
        if chosen_paths:
            viewer.load_image(chosen_paths[0])

    def load_image(self, file_path):
        viewer = self.viewer
        try:
            image = Image.open(file_path)
            if image.mode == "RGBA":
                background = Image.new("RGBA", image.size, (24, 24, 27, 255))
                image = Image.alpha_composite(background, image).convert("RGB")
            elif image.mode != "RGB":
                image = image.convert("RGB")

            viewer.file_path = file_path
            viewer.pil_image = image
            viewer.orig_size = image.size
            viewer.canvas.config(cursor="fleur")
            viewer.btn_close.pack(side=tk.RIGHT, padx=4)
            viewer.fit_to_window()
        except Exception as err:
            messagebox.showerror(
                "Erro ao abrir imagem",
                f"Não foi possível abrir o arquivo selecionado:\n{err}",
            )

    def close_image(self):
        viewer = self.viewer
        viewer.file_path = None
        viewer.pil_image = None
        viewer.tk_image = None
        viewer.tk_legend = None
        viewer.orig_size = (0, 0)
        viewer.scale = 1.0
        viewer.offset_x = 0.0
        viewer.offset_y = 0.0
        viewer.btn_close.pack_forget()
        viewer.lbl_title.config(text=viewer.title)
        viewer.canvas.config(cursor="arrow")
        viewer.render()
