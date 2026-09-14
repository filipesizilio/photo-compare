"""
================================================================================
Módulo: viewer_coordinator.py
Descrição: Coordenação dos visualizadores (sincronização de pan/zoom, alinhamento,
           ajuste à tela, reset 100%).
================================================================================
"""


class ViewerCoordinator:
    """Coordena a sincronização e alinhamento entre visualizadores."""

    def __init__(self, viewers, callbacks):
        self.viewers = viewers  # dict com viewer1, viewer2, viewer3
        self.callbacks = callbacks
        self.sync_locked = True
        self.third_column_visible = False

    def get_visible_viewers(self):
        """Retorna lista dos visualizadores visíveis no momento."""
        viewers = [self.viewers['viewer1'], self.viewers['viewer2']]
        if self.third_column_visible:
            viewers.append(self.viewers['viewer3'])
        return viewers

    def set_sync_locked(self, locked):
        """Define o estado de sincronização."""
        self.sync_locked = locked

    def set_third_column_visible(self, visible):
        """Atualiza o estado de visibilidade da terceira coluna."""
        self.third_column_visible = visible

    # Callbacks de sincronização acionados pelos visualizadores
    def on_viewer_pan(self, source_viewer, dx, dy):
        """Espelha o deslocamento de pan para as outras colunas se travado."""
        if not self.sync_locked:
            return

        for viewer in self.get_visible_viewers():
            if viewer is not source_viewer and viewer.pil_image:
                viewer.pan(dx, dy, trigger_callback=False)

    def on_viewer_zoom(self, source_viewer, factor, mouse_x, mouse_y):
        """Espelha o zoom para as outras colunas proporcionalmente ao centro/cursor."""
        if not self.sync_locked:
            return

        src_w = max(1, source_viewer.canvas.winfo_width())
        src_h = max(1, source_viewer.canvas.winfo_height())
        rel_x = mouse_x / src_w
        rel_y = mouse_y / src_h

        for viewer in self.get_visible_viewers():
            if viewer is not source_viewer and viewer.pil_image:
                tgt_w = max(1, viewer.canvas.winfo_width())
                tgt_h = max(1, viewer.canvas.winfo_height())
                target_x = rel_x * tgt_w
                target_y = rel_y * tgt_h
                viewer.zoom(factor, target_x, target_y, trigger_callback=False)

    def fit_all_to_window(self):
        """Ajusta todas as imagens abertas ao tamanho de seus respectivos canvas."""
        for v in self.get_visible_viewers():
            v.fit_to_window()
        self.callbacks['set_status']("Todas as imagens foram ajustadas à tela.")

    def reset_all_100(self):
        """Redefine o zoom de todas as imagens abertas para 100% (1:1)."""
        for v in self.get_visible_viewers():
            v.reset_100()
        self.callbacks['set_status']("Todas as imagens foram definidas para 100% (1:1).")

    def align_to_first_panel(self):
        """
        Alinha a escala e a posição das outras colunas com base no Painel 1.
        Útil para imagens de resoluções semelhantes precisando de alinhamento imediato.
        """
        ref = self.viewers['viewer1']
        if not ref.pil_image:
            self.callbacks['show_warning'](
                "Aviso",
                "Abra uma imagem no Painel 1 primeiro para usá-lo como referência de alinhamento."
            )
            return

        ref_cw = max(1, ref.canvas.winfo_width())
        ref_ch = max(1, ref.canvas.winfo_height())
        center_img_x = (ref_cw / 2.0 - ref.offset_x) / ref.scale
        center_img_y = (ref_ch / 2.0 - ref.offset_y) / ref.scale

        for viewer in self.get_visible_viewers():
            if viewer is not ref and viewer.pil_image:
                tgt_cw = max(1, viewer.canvas.winfo_width())
                tgt_ch = max(1, viewer.canvas.winfo_height())

                viewer.scale = ref.scale
                viewer.offset_x = tgt_cw / 2.0 - center_img_x * viewer.scale
                viewer.offset_y = tgt_ch / 2.0 - center_img_y * viewer.scale
                viewer.render()

        self.callbacks['set_status']("Todos os painéis foram alinhados com base no Painel 1.")