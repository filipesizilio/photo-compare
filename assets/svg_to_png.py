#!/usr/bin/env python3
"""
Converte um arquivo .svg em .png em um tamanho especificado.

Uso:
    python svg_to_png.py icone.svg 20 20
    python svg_to_png.py icone.svg 40 40 --scale 2

Salva automaticamente como: {nome_arquivo}_{largura}x{altura}.png
"""

import argparse
import sys
from pathlib import Path

try:
    import cairosvg
except ImportError:
    print("Erro: biblioteca 'cairosvg' não encontrada.")
    print("Instale com: pip install cairosvg")
    sys.exit(1)


def converter_svg_para_png(caminho_svg: Path, largura: int, altura: int, scale: int = 1) -> Path:
    if not caminho_svg.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_svg}")

    if caminho_svg.suffix.lower() != ".svg":
        raise ValueError(f"Arquivo precisa ter extensão .svg: {caminho_svg}")

    nome_base = caminho_svg.stem
    caminho_saida = caminho_svg.parent / f"{nome_base}_{largura}x{altura}.png"

    # scale > 1 gera um PNG em resolução maior (supersampling), útil para
    # telas HiDPI, mas o arquivo final ainda é nomeado com o tamanho lógico pedido.
    cairosvg.svg2png(
        url=str(caminho_svg),
        write_to=str(caminho_saida),
        output_width=largura * scale,
        output_height=altura * scale,
    )
    return caminho_saida


def main():
    parser = argparse.ArgumentParser(
        description="Converte um SVG em PNG em um tamanho específico."
    )
    parser.add_argument("arquivo", type=str, help="Caminho do arquivo .svg de entrada")
    parser.add_argument("largura", type=int, help="Largura do PNG de saída, em pixels")
    parser.add_argument("altura", type=int, help="Altura do PNG de saída, em pixels")
    parser.add_argument(
        "--scale",
        type=int,
        default=1,
        help="Fator de supersampling para maior nitidez (ex: 2 = renderiza em 2x e nomeia com o tamanho lógico)",
    )

    args = parser.parse_args()

    if args.largura <= 0 or args.altura <= 0:
        print("Erro: largura e altura devem ser maiores que zero.")
        sys.exit(1)

    caminho_svg = Path(args.arquivo)

    try:
        caminho_saida = converter_svg_para_png(caminho_svg, args.largura, args.altura, args.scale)
    except (FileNotFoundError, ValueError) as e:
        print(f"Erro: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao converter: {e}")
        sys.exit(1)

    print(f"✅ PNG salvo em: {caminho_saida}")


if __name__ == "__main__":
    main()
