"""Renderiza├º├úo e elementos visuais do ImageViewer."""

import os
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont


class ViewerRenderer:
    """Renderiza o viewport e os elementos auxiliares de um visualizador."""

    def __init__(self, viewer):
        self.viewer = viewer

    def render(self):
        viewer = self.viewer
        viewer.canvas.delete("all")

        if not viewer.pil_image:
            self.draw_empty_state()
            self.update_title_zoom()
            return

        canvas_width = viewer.canvas.winfo_width()
        canvas_height = viewer.canvas.winfo_height()
        if canvas_width <= 1 or canvas_height <= 1:
            return

        image_width, image_height = viewer.orig_size
        left = -viewer.offset_x / viewer.scale
        top = -viewer.offset_y / viewer.scale
        right = (canvas_width - viewer.offset_x) / viewer.scale
        bottom = (canvas_height - viewer.offset_y) / viewer.scale

        crop_left = max(0.0, left)
        crop_top = max(0.0, top)
        crop_right = min(float(image_width), right)
        crop_bottom = min(float(image_height), bottom)

        if crop_right > crop_left and crop_bottom > crop_top:
            destination_x = int(round(viewer.offset_x + crop_left * viewer.scale))
            destination_y = int(round(viewer.offset_y + crop_top * viewer.scale))
            destination_width = int(round((crop_right - crop_left) * viewer.scale))
            destination_height = int(round((crop_bottom - crop_top) * viewer.scale))

            if destination_width > 0 and destination_height > 0:
                crop_box = (
                    int(crop_left),
                    int(crop_top),
                    min(image_width, int(crop_right + 0.999999)),
                    min(image_height, int(crop_bottom + 0.999999)),
                )
                try:
                    sub_image = viewer.pil_image.crop(crop_box)
                    resample_mode = (
                        Image.Resampling.NEAREST
                        if viewer.scale >= 4.0
                        else Image.Resampling.BILINEAR
                    )
                    resized = sub_image.resize(
                        (destination_width, destination_height), resample_mode
                    )
                    viewer.tk_image = ImageTk.PhotoImage(resized)
                    viewer.canvas.create_image(
                        destination_x,
                        destination_y,
                        anchor="nw",
                        image=viewer.tk_image,
                    )
                except Exception:
                    pass

        self.draw_overlay_legend(canvas_width, canvas_height)
        self.update_title_zoom()

    def get_image_date(self):
        """Obt├®m a data da imagem a partir do EXIF ou da modifica├º├úo do arquivo."""
        viewer = self.viewer
        if not viewer.file_path or not os.path.exists(viewer.file_path):
            return ""

        try:
            if viewer.pil_image:
                exif = getattr(viewer.pil_image, "getexif", lambda: None)()
                if exif:
                    exif_date = exif.get(36867) or exif.get(306)
                    if exif_date and isinstance(exif_date, str):
                        parts = exif_date.strip().split(" ")
                        if len(parts) == 2:
                            date_parts = parts[0].split(":")
                            if len(date_parts) == 3:
                                return (
                                    f"{date_parts[2]}/{date_parts[1]}/{date_parts[0]} "
                                    f"{parts[1][:5]}"
                                )
        except Exception:
            pass

        try:
            return datetime.fromtimestamp(
                os.path.getmtime(viewer.file_path)
            ).strftime("%d/%m/%Y %H:%M")
        except Exception:
            return ""

    def draw_overlay_legend(self, canvas_width, canvas_height):
        """Desenha a legenda semitransparente com caminho, resolu├º├úo e data."""
        viewer = self.viewer
        if not viewer.file_path or not viewer.pil_image:
            return

        image_width, image_height = viewer.orig_size
        megapixels = (image_width * image_height) / 1_000_000.0
        date_string = self.get_image_date()

        first_line = viewer.file_path
        second_line = f"{megapixels:.1f} MP ({image_width}x{image_height})"
        if date_string:
            second_line += f"   ÔÇó   {date_string}"

        try:
            title_font = ImageFont.truetype("segoeuib.ttf", 11)
            subtitle_font = ImageFont.truetype("segoeui.ttf", 11)
        except Exception:
            try:
                title_font = ImageFont.truetype("segoeui.ttf", 11)
                subtitle_font = title_font
            except Exception:
                title_font = ImageFont.load_default()
                subtitle_font = title_font

        def measure(text, font):
            try:
                bounds = font.getbbox(text)
                return bounds[2] - bounds[0], bounds[3] - bounds[1]
            except Exception:
                return len(text) * 7, 14

        first_width, first_height = measure(first_line, title_font)
        second_width, second_height = measure(second_line, subtitle_font)
        max_line_width = max(160, canvas_width - 40)
        while first_width > max_line_width and len(first_line) > 20:
            first_line = "..." + first_line[6:]
            first_width, first_height = measure(first_line, title_font)

        box_width = max(first_width, second_width) + 20
        box_height = first_height + second_height + 14
        box = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 128))
        draw = ImageDraw.Draw(box)
        draw.text((10, 4), first_line, font=title_font, fill=(255, 255, 255, 255))
        draw.text(
            (10, 6 + first_height + 2),
            second_line,
            font=subtitle_font,
            fill=(235, 235, 235, 225),
        )

        viewer.tk_legend = ImageTk.PhotoImage(box)
        position_y = max(10, canvas_height - box_height - 10)
        viewer.canvas.create_image(
            10, position_y, anchor="nw", image=viewer.tk_legend, tags="legend"
        )
        viewer.canvas.tag_bind("legend", "<ButtonPress-1>", viewer._on_button_press)
        viewer.canvas.tag_bind("legend", "<B1-Motion>", viewer._on_mouse_drag)
        viewer.canvas.tag_bind("legend", "<ButtonRelease-1>", viewer._on_button_release)
        viewer.canvas.tag_bind(
            "legend", "<Double-Button-1>", lambda event: viewer.fit_to_window()
        )

    def draw_empty_state(self):
        """Desenha a mensagem de instru├º├úo quando n├úo h├í imagem carregada."""
        viewer = self.viewer
        canvas_width = viewer.canvas.winfo_width() or 400
        canvas_height = viewer.canvas.winfo_height() or 400
        center_x, center_y = canvas_width // 2, canvas_height // 2
        padding = 20

        viewer.canvas.create_rectangle(
            padding,
            padding,
            canvas_width - padding,
            canvas_height - padding,
            outline="#3f3f46",
            dash=(4, 4),
            width=1,
            tags="empty",
        )
        viewer.canvas.create_text(
            center_x,
            center_y - 20,
            text="­ƒôé Clique para abrir ou arraste arquivos aqui",
            font=("Segoe UI", 12, "bold"),
            fill="#71717a",
            tags="empty",
        )
        viewer.canvas.create_text(
            center_x,
            center_y + 16,
            text="Selecione at├® 3 fotos ou solte do Windows Explorer\nArraste com o mouse para mover ÔÇó Roda para zoom",
            font=("Segoe UI", 9),
            fill="#52525b",
            justify=tk.CENTER,
            tags="empty",
        )

    def update_title_zoom(self):
        """Atualiza o n├¡vel de zoom exibido no t├¡tulo da coluna."""
        viewer = self.viewer
        if not viewer.pil_image:
            viewer.lbl_title.config(text=viewer.title)
        else:
            zoom_percent = int(round(viewer.scale * 100))
            viewer.lbl_title.config(text=f"{viewer.title}  ÔÇó  {zoom_percent}%")
