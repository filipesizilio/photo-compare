"""
================================================================================
Módulo: exif_core.py
Descrição: Operações fundamentais de leitura, escrita e manipulação de dados EXIF.
================================================================================
"""

import os
from PIL import Image, ExifTags


def _get_exif_data(image_path: str) -> dict:
    """
    Obtém os dados EXIF de uma imagem.

    Args:
        image_path (str): Caminho para a imagem.

    Returns:
        dict: Dicionário contendo os dados EXIF.
    """
    exif_data = {}
    try:
        with Image.open(image_path) as img:
            info = img._getexif()
            if info:
                for tag, value in info.items():
                    decoded_tag = ExifTags.TAGS.get(tag, tag)
                    exif_data[decoded_tag] = value
            else:
                print("Nenhum dado EXIF encontrado.")
    except Exception as e:
        print(f"Erro ao obter dados EXIF: {e}")

    return exif_data


def _transfer_exif_data(original_image_path: str, output_image_pil: Image.Image, software_name: str) -> Image.Image:
    """
    Transfere dados EXIF da imagem original para a imagem de saída (PIL Image).
    Também atualiza o campo 'Software' com o nome do programa.

    Args:
        original_image_path (str): Caminho para a imagem original.
        output_image_pil (PIL.Image.Image): A imagem PIL que será salva (com estilo aplicado).
        software_name (str): O nome do programa/script a ser inserido no campo 'Software' do EXIF.

    Returns:
        PIL.Image.Image: A imagem PIL com os dados EXIF atualizados.
    """
    try:
        # Abre a imagem original para ler os dados EXIF
        with Image.open(original_image_path) as img_original:
            exif_data = img_original.info.get('exif')  # Obtém os dados EXIF brutos

            if exif_data:
                # Se houver dados EXIF, tenta criar um dicionário mais legível
                decoded_exif = {}
                for tag, value in img_original._getexif().items():
                    decoded_tag = ExifTags.TAGS.get(tag, tag)
                    decoded_exif[decoded_tag] = value

                # Atualiza o campo 'Software'
                decoded_exif['Software'] = software_name

                # Reconverte o dicionário EXIF para o formato que o Pillow espera para salvar
                # Vamos usar img_original.info para obter o raw exif bytes
                # E então usar piexif para manipular.
                # MAS, como o objetivo é didático e manter a dependência mínima,
                # se o campo 'Software' já existe, o Pillow pode sobrescrever com info['exif']
                # Se não, ou se queremos adicionar novas tags, é mais complicado sem piexif.

                # Para a tag 'Software', podemos sobrescrevê-la no info.
                # Primeiro, tentamos obter a data EXIF existente em bytes.
                exif_bytes = img_original.info.get('exif')

                if exif_bytes:
                    # Se houver dados EXIF, vamos carregá-los com piexif, modificar e depois salvar.
                    # Isso requer a instalação de piexif: pip install piexif
                    import piexif
                    exif_dict = piexif.load(exif_bytes)

                    # Atualiza a tag Software (IFD0, Tag 305)
                    # Convertendo a string para bytes, como piexif espera
                    exif_dict["0th"][piexif.ImageIFD.Software] = software_name.encode('utf-8')

                    # Vamos garantir que os dados de rotação sejam mantidos
                    if "Orientation" in exif_dict["0th"]:
                        exif_dict["0th"][piexif.ImageIFD.Orientation] = exif_dict["0th"][piexif.ImageIFD.Orientation]

                    # Converte o dicionário EXIF de volta para bytes
                    exif_bytes = piexif.dump(exif_dict)

                    # Anexa os dados EXIF atualizados à imagem de saída
                    output_image_pil.info['exif'] = exif_bytes
                else:
                    # Se não houver dados EXIF, cria um novo conjunto mínimo com a tag Software
                    import piexif
                    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
                    exif_dict["0th"][piexif.ImageIFD.Software] = software_name.encode('utf-8')
                    exif_bytes = piexif.dump(exif_dict)
                    output_image_pil.info['exif'] = exif_bytes

                print(f"Dados EXIF transferidos e campo 'Software' atualizado para '{software_name}'.")
            else:
                print("Nenhum dado EXIF encontrado na imagem original para transferir.")
                # Ainda podemos adicionar a tag Software se não houver EXIF nenhum
                import piexif
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
                exif_dict["0th"][piexif.ImageIFD.Software] = software_name.encode('utf-8')
                exif_bytes = piexif.dump(exif_dict)
                output_image_pil.info['exif'] = exif_bytes
                print(f"Campo 'Software' adicionado para '{software_name}'.")

    except Exception as e:
        print(f"Erro ao transferir dados EXIF: {e}")

    return output_image_pil


def _clean_exif_data(image_path: str, output_path: str):
    """
    Remove todos os dados EXIF de uma imagem e salva a imagem limpa.

    Args:
        image_path (str): Caminho para a imagem original.
        output_path (str): Caminho onde a imagem limpa será salva.
    """
    # Refatorar a função para usar piexif para garantir a manipulação e remoção apenas dos dados EXIF sem alterar os pixels da imagem
    # Isso é mais seguro do que reabrir e salvar a imagem diretamente, o que pode alterar a qualidade.
    # Para a tag 'Software', podemos sobrescrevê-la no info.
    # Primeiro, tentamos obter a data EXIF existente em bytes.

    # Se houver dados EXIF, vamos carregá-los com piexif, modificar e depois salvar.
    # Isso requer a instalação de piexif: pip install piexif
    import piexif

    try:
        with Image.open(image_path) as img:
            exif_bytes = img._getexif()
            if exif_bytes:
                exif_dict = piexif.load(exif_bytes)
                exif_dict["0th"] = {}
                exif_dict["Exif"] = {}
                exif_dict["GPS"] = {}
                exif_dict["Interop"] = {}
                exif_dict["1st"] = {}
                exif_dict["thumbnail"] = None
                # Asegura que os dados de rotação sejam mantidos
                if "Orientation" in exif_dict["0th"]:
                    exif_dict["0th"][piexif.ImageIFD.Orientation] = exif_dict["0th"][piexif.ImageIFD.Orientation]

                # Converte o dicionário EXIF de volta para bytes
                exif_bytes = piexif.dump(exif_dict)
                img.save(output_path, exif=exif_bytes)
                print(f"Imagem salva sem dados EXIF em: {output_path}")
            else:
                print("Nenhum dado EXIF encontrado para limpar.")
    except Exception as e:
        print(f"Erro ao limpar dados EXIF: {e}")
        print("Tentando método alternativo de limpeza (pode alterar a qualidade da imagem)...")
        # Método original (menos seguro, pode alterar a qualidade da imagem)
        try:
            with Image.open(image_path) as img:
                # Salva a imagem sem dados EXIF
                img.save(output_path)
                print(f"Imagem salva sem dados EXIF em: {output_path}")
        except Exception as e:
            print(f"Erro no metodo alternativo ao limpar dados EXIF: {e}")


def copy_exif_tags_between_images(from_path: str, to_path: str, selected_tags: list) -> bool:
    """
    Copia tags EXIF específicas de uma imagem para outra.

    Args:
        from_path: Caminho da imagem de origem
        to_path: Caminho da imagem de destino
        selected_tags: Lista de nomes de tags EXIF a copiar

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        import piexif

        # Carrega EXIF da origem
        with Image.open(from_path) as img:
            exif_bytes = img.info.get('exif')
            if not exif_bytes:
                return False
            from_exif_dict = piexif.load(exif_bytes)

        # Mapeia nomes de tags para IDs
        tag_to_ifd = {}
        for ifd_name in ["0th", "Exif", "GPS", "Interop", "1st"]:
            if ifd_name in from_exif_dict:
                for tag_id, value in from_exif_dict[ifd_name].items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    tag_to_ifd[tag_name] = (ifd_name, tag_id, value)

        # Carrega EXIF do destino
        with Image.open(to_path) as img:
            exif_bytes = img.info.get('exif')
            if exif_bytes:
                to_exif_dict = piexif.load(exif_bytes)
            else:
                to_exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

            # Copia apenas as tags selecionadas
            for tag in selected_tags:
                if tag in tag_to_ifd:
                    ifd_name, tag_id, value = tag_to_ifd[tag]
                    to_exif_dict[ifd_name][tag_id] = value

            # Salva
            exif_bytes = piexif.dump(to_exif_dict)
            img.save(to_path, exif=exif_bytes)

        return True
    except Exception as e:
        print(f"Erro ao copiar EXIF: {e}")
        return False