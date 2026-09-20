"""
Teste automatizado para validação do novo sistema unificado de metadados EXIF.
"""

import os
import tempfile
from PIL import Image
import piexif

from exif_models import ImageCardInfo, ExifCompareState
from exif_copy import execute_planned_exif_transfers, check_file_exif_writable


class DummyViewer:
    def __init__(self, path, title):
        self.file_path = path
        self.title = title
        with Image.open(path) as img:
            self.orig_size = img.size
            self.pil_image = img.copy()


def run_exif_tests():
    print("Iniciando testes da nova interface e lógica EXIF...")

    with tempfile.TemporaryDirectory() as tmpdir:
        img_a_path = os.path.join(tmpdir, "img_a.jpg")
        img_b_path = os.path.join(tmpdir, "img_b.jpg")
        img_c_path = os.path.join(tmpdir, "img_c.jpg")

        # Cria 3 imagens JPEG válidas
        img_a = Image.new("RGB", (400, 300), color="blue")
        img_b = Image.new("RGB", (500, 400), color="purple")
        img_c = Image.new("RGB", (600, 500), color="teal")

        # Insere EXIF sintético em A e B
        exif_dict_a = {
            "0th": {
                piexif.ImageIFD.Make: b"Sony",
                piexif.ImageIFD.Model: b"Alpha 7 IV",
            },
            "Exif": {
                piexif.ExifIFD.FNumber: (28, 10),  # f/2.8
                piexif.ExifIFD.ISOSpeedRatings: 400,
            }
        }
        exif_dict_b = {
            "0th": {
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"EOS R5",
            },
            "Exif": {
                piexif.ExifIFD.FNumber: (40, 10),  # f/4.0
                piexif.ExifIFD.ISOSpeedRatings: 800,
            }
        }

        img_a.save(img_a_path, exif=piexif.dump(exif_dict_a))
        img_b.save(img_b_path, exif=piexif.dump(exif_dict_b))
        img_c.save(img_c_path)  # Imagem C sem EXIF inicial

        img_a.close()
        img_b.close()
        img_c.close()

        viewer_a = DummyViewer(img_a_path, "Imagem A")
        viewer_b = DummyViewer(img_b_path, "Imagem B")
        viewer_c = DummyViewer(img_c_path, "Imagem C")

        # 1. Teste de criação dos cards
        card_a = ImageCardInfo("A", viewer_a)
        card_b = ImageCardInfo("B", viewer_b)
        card_c = ImageCardInfo("C", viewer_c)

        assert card_a.has_exif is True, "Card A deveria ter EXIF"
        assert card_b.has_exif is True, "Card B deveria ter EXIF"
        assert card_c.has_exif is False, "Card C não deveria ter EXIF inicial"
        print("[OK] Teste 1: ImageCardInfo e leitura de metadados OK")

        # 2. Teste do estado comparativo ExifCompareState com 3 imagens
        cards = {"A": card_a, "B": card_b, "C": card_c}
        state = ExifCompareState(cards)

        assert "Make" in state.all_tags, "Tag 'Make' deveria estar na lista de tags"
        assert "Model" in state.all_tags, "Tag 'Model' deveria estar na lista de tags"
        assert state.is_tag_different("Make") is True, "'Make' difere entre A e B"
        print("[OK] Teste 2: ExifCompareState e identificação de diferenças OK")

        # 3. Teste de aplicação global e bloqueio de origem como destino
        state.apply_global_source_dest("A", "ALL")
        row_make = state.row_states["Make"]
        assert row_make.source == "A", "Origem de Make deveria ser A"
        assert "A" not in row_make.destinations, "Origem A NUNCA pode ser destino"
        assert "B" in row_make.destinations, "B deve ser destino"
        assert "C" in row_make.destinations, "C deve ser destino"
        print("[OK] Teste 3: Regra de bloqueio de origem como destino OK")

        # 4. Teste do Resumo da Operação
        state.set_all_selected(True)
        summary = state.compute_summary()
        assert summary["selected_count"] > 0, "Deveria haver tags selecionadas"
        assert summary["transfers_count"] > 0, "Deveria haver transferências programadas"
        assert summary["overwrites_count"] > 0, "Deveria acusar sobrescrita em tags existentes de B"
        print(f"[OK] Teste 4: Resumo da Operação (Tags: {summary['selected_count']}, Transferências: {summary['transfers_count']}, Sobrescritas: {summary['overwrites_count']}) OK")

        # 5. Teste de gravação real com execute_planned_exif_transfers
        res = execute_planned_exif_transfers(state)
        assert res["success"] is True, f"Gravação falhou: {res['errors']}"
        assert len(res["modified_destinations"]) >= 2, "Deveria ter modificado B e C"

        # Verifica se Imagem C agora recebeu o Make "Sony" vindo de A
        card_c_after = ImageCardInfo("C", viewer_c)
        assert card_c_after.has_exif is True, "Imagem C agora deveria ter EXIF gravado"
        make_val = card_c_after.exif_data.get("Make")
        assert make_val in ("Sony", b"Sony"), f"Imagem C deveria ter recebido Make Sony, obtido: {make_val}"
        print("[OK] Teste 5: Transferência física de EXIF para destinos B e C concluída com sucesso!")

    print("\nTODOS OS TESTES ESPECÍFICOS DE EXIF PASSARAM COM SUCESSO!")


if __name__ == "__main__":
    run_exif_tests()
