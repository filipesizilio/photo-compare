"""
Testes automatizados para o Photo Compare:
- Teste de instanciação das janelas e componentes
- Carregamento de imagens sintéticas
- Teste de pan e zoom sincronizados e destravados
- Teste de adição e remoção dinâmica da 3ª coluna
- Teste de alinhamento com base no painel 1
"""

import os
import tempfile
from PIL import Image, ImageDraw
from main import PhotoCompareApp


def create_dummy_image(path, width, height, color, label):
    img = Image.new("RGB", (width, height), color=color)
    draw = ImageDraw.Draw(img)
    # Desenha cruz e retângulo para referência visual
    draw.line((0, 0, width, height), fill="white", width=4)
    draw.line((0, height, width, 0), fill="white", width=4)
    draw.rectangle((50, 50, width - 50, height - 50), outline="yellow", width=6)
    img.save(path)


def run_tests():
    print("Iniciando testes de verificação do Photo Compare...")

    with tempfile.TemporaryDirectory() as tmpdir:
        img1_path = os.path.join(tmpdir, "img1.png")
        img2_path = os.path.join(tmpdir, "img2.png")
        img3_path = os.path.join(tmpdir, "img3.png")

        create_dummy_image(img1_path, 800, 600, (40, 70, 150), "Image 1")
        create_dummy_image(img2_path, 800, 600, (150, 40, 40), "Image 2")
        create_dummy_image(img3_path, 1200, 900, (40, 150, 60), "Image 3")

        app = PhotoCompareApp()
        app.update()  # Processa eventos iniciais do Tkinter

        # 1. Verifica estado inicial
        assert len(app.get_visible_viewers()) == 2, "Deveriam existir exatamente 2 colunas visíveis inicialmente"
        assert app.sync_locked is True, "Sincronização deveria iniciar travada"
        print("[OK] Teste 1: Estado inicial com 2 colunas e sincronizacao ativa OK")

        # 2. Carrega imagens nos 2 visualizadores
        app.viewer1.load_image(img1_path)
        app.viewer2.load_image(img2_path)
        app.update()

        assert app.viewer1.pil_image is not None, "Imagem 1 não foi carregada"
        assert app.viewer2.pil_image is not None, "Imagem 2 não foi carregada"
        print("[OK] Teste 2: Carregamento de imagens nas 2 primeiras colunas OK")

        # 3. Teste de Pan sincronizado
        initial_offset_x2 = app.viewer2.offset_x
        initial_offset_y2 = app.viewer2.offset_y

        app.viewer1.pan(50, 30, trigger_callback=True)
        app.update()

        assert app.viewer2.offset_x == initial_offset_x2 + 50, f"Offset X do viewer 2 deveria ter avançado 50. Atual: {app.viewer2.offset_x}"
        assert app.viewer2.offset_y == initial_offset_y2 + 30, f"Offset Y do viewer 2 deveria ter avançado 30. Atual: {app.viewer2.offset_y}"
        print("[OK] Teste 3: Pan sincronizado propagado para a segunda coluna OK")

        # 4. Teste de Zoom sincronizado
        initial_scale2 = app.viewer2.scale
        app.viewer1.zoom(1.2, mouse_x=200, mouse_y=200, trigger_callback=True)
        app.update()

        assert abs(app.viewer2.scale - initial_scale2 * 1.2) < 1e-4, f"Escala do viewer 2 deveria ser {initial_scale2 * 1.2}, mas é {app.viewer2.scale}"
        print("[OK] Teste 4: Zoom sincronizado propagado para a segunda coluna OK")

        # 5. Teste de Destrava da Sincronização
        app.toggle_sync()
        assert app.sync_locked is False, "Sincronização deveria estar destravada"

        prev_scale2 = app.viewer2.scale
        app.viewer1.zoom(1.5, mouse_x=100, mouse_y=100, trigger_callback=True)
        app.update()

        assert app.viewer2.scale == prev_scale2, "Quando destravado, zoom do viewer 1 não deve alterar o viewer 2"
        print("[OK] Teste 5: Modo destravado não propaga alterações OK")

        # 6. Teste da 3ª Coluna
        app.toggle_sync()  # Volta a travar
        app.toggle_third_column()
        app.update()

        assert app.third_column_visible is True, "3ª coluna deveria estar visível"
        assert len(app.get_visible_viewers()) == 3, "Deveriam existir 3 colunas visíveis"

        app.viewer3.load_image(img3_path)
        app.update()

        assert app.viewer3.pil_image is not None, "Imagem 3 não foi carregada na 3ª coluna"
        print("[OK] Teste 6: Abertura da 3ª coluna e carregamento de imagem OK")

        # 7. Teste de Pan sincronizado com 3 colunas
        v2_x_before = app.viewer2.offset_x
        v3_x_before = app.viewer3.offset_x

        app.viewer1.pan(-25, 10, trigger_callback=True)
        app.update()

        assert app.viewer2.offset_x == v2_x_before - 25
        assert app.viewer3.offset_x == v3_x_before - 25
        print("[OK] Teste 7: Pan sincronizado nas 3 colunas simultaneamente OK")

        # 8. Teste do botão Alinhar ao Painel 1
        app.align_to_first_panel()
        app.update()
        assert app.viewer2.scale == app.viewer1.scale, "Viewer 2 deveria adotar a mesma escala do Viewer 1"
        assert app.viewer3.scale == app.viewer1.scale, "Viewer 3 deveria adotar a mesma escala do Viewer 1"
        print("[OK] Teste 8: Alinhamento geral baseado no Painel 1 OK")

        # 9. Teste de remoção da 3ª coluna
        app.toggle_third_column()
        app.update()
        assert app.third_column_visible is False, "3ª coluna deveria estar oculta"
        assert len(app.get_visible_viewers()) == 2, "Deveriam existir 2 colunas ativas após fechar a 3ª"
        print("[OK] Teste 9: Ocultação da 3ª coluna com restauração do layout OK")

        # 10. Teste de fechar imagem (limpar)
        app.viewer1.close_image()
        app.update()
        assert app.viewer1.pil_image is None, "Viewer 1 deveria estar sem imagem"
        print("[OK] Teste 10: Limpeza de imagem OK")

        app.destroy()

    print("\nTODOS OS 10 TESTES PASSARAM COM SUCESSO!")


if __name__ == "__main__":
    run_tests()
