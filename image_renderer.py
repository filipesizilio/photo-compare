"""Renderiza├º├úo e elementos visuais do ImageViewer."""

import os
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageColor
from app_config import (
    COLOR_EMPTY_STATE_BORDER,
    COLOR_EMPTY_STATE_TEXT,
    COLOR_EMPTY_STATE_SUBTEXT,
    COLOR_OVERLAY_BG,
    COLOR_OVERLAY_TEXT,
    COLOR_OVERLAY_SUBTEXT,
    OVERLAY_ALPHA,
    get_mode_color,
)


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
            second_line += f"   •   {date_string}"

        try:
            title_font = ImageFont.truetype("segoeuib.ttf", 14)
            subtitle_font = ImageFont.truetype("segoeui.ttf", 13)
        except Exception:
            try:
                title_font = ImageFont.truetype("segoeui.ttf", 14)
                subtitle_font = title_font
            except Exception:
                title_font = ImageFont.load_default()
                subtitle_font = title_font

        def measure(text, font):
            try:
                bounds = font.getbbox(text)
                return bounds[2] - bounds[0], bounds[3] - bounds[1]
            except Exception:
                return len(text) * 8, 16

        first_width, first_height = measure(first_line, title_font)
        second_width, second_height = measure(second_line, subtitle_font)
        max_line_width = max(160, canvas_width - 40)
        while first_width > max_line_width and len(first_line) > 20:
            first_line = "..." + first_line[6:]
            first_width, first_height = measure(first_line, title_font)

        padding_x = 12
        padding_y = 8
        spacing_between_lines = 4

        bg_hex = get_mode_color(COLOR_OVERLAY_BG)
        text_hex = get_mode_color(COLOR_OVERLAY_TEXT)
        subtext_hex = get_mode_color(COLOR_OVERLAY_SUBTEXT)

        try:
            bg_rgb = ImageColor.getrgb(bg_hex)
        except Exception:
            bg_rgb = (0, 0, 0)
        alpha = int(max(0.0, min(1.0, float(OVERLAY_ALPHA))) * 255)
        bg_rgba = (bg_rgb[0], bg_rgb[1], bg_rgb[2], alpha)

        try:
            text_rgb = ImageColor.getrgb(text_hex)
            text_fill = (text_rgb[0], text_rgb[1], text_rgb[2], 255)
        except Exception:
            text_fill = (255, 255, 255, 255)

        try:
            subtext_rgb = ImageColor.getrgb(subtext_hex)
            subtext_fill = (subtext_rgb[0], subtext_rgb[1], subtext_rgb[2], 230)
        except Exception:
            subtext_fill = (235, 235, 235, 225)

        box_width = max(first_width, second_width) + (padding_x * 2)
        box_height = first_height + second_height + (padding_y * 2) + spacing_between_lines
        box = Image.new("RGBA", (box_width, box_height), bg_rgba)
        draw = ImageDraw.Draw(box)
        draw.text((padding_x, padding_y), first_line, font=title_font, fill=text_fill)
        draw.text(
            (padding_x, padding_y + first_height + spacing_between_lines),
            second_line,
            font=subtitle_font,
            fill=subtext_fill,
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
        """Desenha a mensagem de instrução quando não há imagem carregada."""
        viewer = self.viewer
        viewer.canvas.delete("empty")
        canvas_width = viewer.canvas.winfo_width() or 400
        canvas_height = viewer.canvas.winfo_height() or 400
        center_x, center_y = canvas_width // 2, canvas_height // 2
        padding = 20

        border_color = get_mode_color(COLOR_EMPTY_STATE_BORDER)
        text_color = get_mode_color(COLOR_EMPTY_STATE_TEXT)
        subtext_color = get_mode_color(COLOR_EMPTY_STATE_SUBTEXT)

        viewer.canvas.create_rectangle(
            padding,
            padding,
            canvas_width - padding,
            canvas_height - padding,
            outline=border_color,
            dash=(4, 4),
            width=1,
            tags="empty",
        )
        viewer.canvas.create_text(
            center_x,
            center_y - 20,
            text="📂 Clique para abrir ou arraste arquivos aqui",
            font=("Segoe UI", 12, "bold"),
            fill=text_color,
            tags="empty",
        )
        viewer.canvas.create_text(
            center_x,
            center_y + 16,
            text="Selecione até 3 fotos ou solte do Windows Explorer\nArraste com o mouse para mover • Roda para zoom",
            font=("Segoe UI", 9),
            fill=subtext_color,
            justify=tk.CENTER,
            tags="empty",
        )

    def update_title_zoom(self):
        """Atualiza o nível de zoom exibido no título da coluna."""
        viewer = self.viewer
        if not viewer.pil_image:
            viewer.lbl_title.config(text=viewer.title)
        else:
            zoom_percent = int(round(viewer.scale * 100))
            viewer.lbl_title.config(text=f"{viewer.title}  •  {zoom_percent}%")
