"""
================================================================================
Módulo: exif_gps.py
Descrição: Funções para manipulação de dados GPS em metadados EXIF.
================================================================================
"""

from PIL import Image, ExifTags


def _gps_to_gmaps(gps_info: dict) -> str:
    """
    Converte informações GPS EXIF em um link do Google Maps.

    Args:
        gps_info (dict): Dicionário contendo informações GPS EXIF.

    Returns:
        str: URL do Google Maps com a localização.
    """
    try:
        required_keys = [1, 2, 3, 4]  # GPSLatitudeRef, GPSLatitude, GPSLongitudeRef, GPSLongitude
        for key in required_keys:
            if key not in gps_info:
                raise ValueError(f"Chave GPS {key} ausente nos dados EXIF.")

        # Refatorar a função:
        # *** Está retornando erro 'IFDRational' object is not subscriptable
        # - Verifica se as chaves necessárias estão presentes
        # - Ajustar para trabalhar com diferentes formatos de dados de localização
        # Mantendo aqui para referência futura.
        def _convert_to_degrees(value):
            d, m, s = value
            return d[0] / d[1] + (m[0] / m[1]) / 60 + (s[0] / s[1]) / 3600

        # Converte a latitude e longitude para graus decimais
        #   Refatorar a função para evitar o erro 'IFDRational' object is not subscriptable
        #   GPSLatitude e GPSLongitude são tuplas de tuplas representando graus, minutos e segundos
        #   Exemplo: ((34, 1), (3, 1), (30, 1)) para 34° 3' 30''
        #   GPSLatitudeRef e GPSLongitudeRef são strings 'N', 'S', 'E', 'W'
        #   A função _convert_to_degrees_refactor assume que value é uma tupla de três elementos (graus, minutos, segundos)
        #
        #  -> Essa abordagem  funcionou.
        def _convert_to_degrees_refactor(value):
            d = value[0]
            m = value[1]
            s = value[2]
            return d + (m / 60.0) + (s / 3600.0)

        lat = _convert_to_degrees_refactor(gps_info[2])
        if gps_info[1] == 'S':
            lat = -lat

        lon = _convert_to_degrees_refactor(gps_info[4])
        if gps_info[3] == 'W':
            lon = -lon

        # Debug
        # print(f"Lat: {lat}, Lon: {lon}", flush=True)

        return f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
    except Exception as e:
        print(f"Erro ao converter dados GPS para link do Google Maps: {e}")
        return ""


def _write_gps_to_exif(image_path: str, output_path: str, latitude: float, longitude: float, altitude: float = 0.0):
    """
    Adiciona informações de localização ao EXIF de uma imagem.

    Args:
        image_path (str): Caminho para a imagem original.
        output_path (str): Caminho onde a imagem com dados EXIF será salva.
        latitude (float): Latitude da localização.
        longitude (float): Longitude da localização.
        altitude (float, optional): Altitude da localização. Default is 0.0.
    """
    try:
        with Image.open(image_path) as img:
            import piexif
            exif_bytes = img.info.get('exif')
            if exif_bytes:
                exif_dict = piexif.load(exif_bytes)
            else:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}

            # Função para converter graus decimais para o formato (graus, minutos, segundos) em frações
            def _deg_to_dms_rational(deg_float):
                import fractions
                deg_abs = abs(deg_float)
                deg = int(deg_abs)
                min_float = (deg_abs - deg) * 60
                minute = int(min_float)
                sec_float = (min_float - minute) * 60
                sec = sec_float
                return [
                    (deg, 1),
                    (minute, 1),
                    (int(sec * 1000000), 1000000)
                ]

            # Latitude e longitude em graus decimais
            lat_ref = 'N' if latitude >= 0 else 'S'
            lon_ref = 'E' if longitude >= 0 else 'W'
            lat_dms = _deg_to_dms_rational(latitude)
            lon_dms = _deg_to_dms_rational(longitude)

            if altitude == 0.0:
                alt_value = exif_dict["GPS"].get(piexif.GPSIFD.GPSAltitude, 0.0)
                if isinstance(alt_value, tuple) and len(alt_value) == 2 and alt_value[1] != 0:
                    altitude = float(alt_value[0]) / float(alt_value[1])
                elif isinstance(alt_value, (int, float)):
                    altitude = float(alt_value)
                else:
                    altitude = 0.0
            else:
                altitude = altitude

            gps_ifd = {
                piexif.GPSIFD.GPSLatitudeRef: lat_ref.encode(),
                piexif.GPSIFD.GPSLatitude: lat_dms,
                piexif.GPSIFD.GPSLongitudeRef: lon_ref.encode(),
                piexif.GPSIFD.GPSLongitude: lon_dms,
                piexif.GPSIFD.GPSAltitudeRef: 0,
                piexif.GPSIFD.GPSAltitude: (int(abs(altitude) * 1000000), 1000000),
                piexif.GPSIFD.GPSMapDatum: b"WGS-84",
                piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
            }

            exif_dict["GPS"] = gps_ifd

            exif_bytes = piexif.dump(exif_dict)
            img.save(output_path, exif=exif_bytes)
            print(f"Imagem salva com dados de localização em: {output_path}")
    except Exception as e:
        print(f"Erro ao escrever dados GPS no EXIF: {e}")