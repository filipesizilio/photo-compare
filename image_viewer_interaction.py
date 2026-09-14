"""Interação, zoom e pan do widget ImageViewer."""

from PIL import Image


class ViewerInteraction:
    """Implementa operações de viewport e handlers de mouse."""

    def __init__(self, viewer):
        self.viewer = viewer

    def rotate_90(self):
        viewer = self.viewer
        if not viewer.pil_image:
            return

        canvas_width = viewer.canvas.winfo_width()
        canvas_height = viewer.canvas.winfo_height()
        image_width, image_height = viewer.orig_size
        center_x = viewer.offset_x + (image_width * viewer.scale) / 2.0
        center_y = viewer.offset_y + (image_height * viewer.scale) / 2.0
        viewer.pil_image = viewer.pil_image.transpose(Image.Transpose.ROTATE_270)
        viewer.orig_size = viewer.pil_image.size
        new_width, new_height = viewer.orig_size
        viewer.offset_x = center_x - (new_width * viewer.scale) / 2.0
        viewer.offset_y = center_y - (new_height * viewer.scale) / 2.0
        viewer.render()

    def zoom(self, factor, mouse_x, mouse_y, trigger_callback=True):
        viewer = self.viewer
        if not viewer.pil_image:
            return

        new_scale = max(viewer.MIN_SCALE, min(viewer.MAX_SCALE, viewer.scale * factor))
        if abs(new_scale - viewer.scale) < 1e-6:
            return

        actual_factor = new_scale / viewer.scale
        viewer.offset_x = mouse_x - (mouse_x - viewer.offset_x) * actual_factor
        viewer.offset_y = mouse_y - (mouse_y - viewer.offset_y) * actual_factor
        viewer.scale = new_scale
        viewer.render()

        if trigger_callback and viewer.on_zoom_callback:
            viewer.on_zoom_callback(viewer, factor, mouse_x, mouse_y)

    def pan(self, dx, dy, trigger_callback=True):
        viewer = self.viewer
        if not viewer.pil_image:
            return

        viewer.offset_x += dx
        viewer.offset_y += dy
        viewer.render()
        if trigger_callback and viewer.on_pan_callback:
            viewer.on_pan_callback(viewer, dx, dy)

    def on_button_press(self, event):
        viewer = self.viewer
        if not viewer.pil_image:
            viewer.open_file_dialog()
            return
        viewer._is_dragging = True
        viewer._drag_start_x = event.x
        viewer._drag_start_y = event.y

    def on_mouse_drag(self, event):
        viewer = self.viewer
        if not viewer._is_dragging or not viewer.pil_image:
            return
        delta_x = event.x - viewer._drag_start_x
        delta_y = event.y - viewer._drag_start_y
        viewer._drag_start_x = event.x
        viewer._drag_start_y = event.y
        self.pan(delta_x, delta_y, trigger_callback=True)

    def on_button_release(self, event):
        self.viewer._is_dragging = False

    def on_mouse_wheel(self, event):
        viewer = self.viewer
        if not viewer.pil_image or event.delta == 0:
            return
        steps = max(-3.0, min(3.0, event.delta / 120.0))
        self.zoom(viewer.ZOOM_IN_FACTOR ** steps, event.x, event.y, trigger_callback=True)

    def on_mouse_wheel_linux(self, event, direction):
        viewer = self.viewer
        if viewer.pil_image:
            factor = viewer.ZOOM_IN_FACTOR if direction > 0 else viewer.ZOOM_OUT_FACTOR
            self.zoom(factor, event.x, event.y, trigger_callback=True)

    def on_resize(self, event):
        self.viewer.render()
