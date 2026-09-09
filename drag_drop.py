"""
================================================================================
Projeto: Photo Compare
Descrição: Ferramenta desktop para comparação visual simultânea de imagens lado a
           lado (2 ou 3 colunas) com suporte a pan e zoom sincronizados ou
           independentes, arrastar e soltar (Drag & Drop) nativo do Windows e
           renderização de alto desempenho via Pillow.

Arquivo: drag_drop.py
Função do Script:
    Módulo de integração com Drag & Drop nativo do Windows para janelas Tkinter.

    Utiliza a biblioteca `tkinterdnd2` que fornece suporte nativo a Drag & Drop
    para Tkinter via Tcl/Tk extension, evitando problemas de GIL e threading
    que afetam abordagens baseadas em windnd ou Win32 API direta.

    Como fallback (plataformas não-Windows ou tkinterdnd2 indisponível), a função
    retorna False sem gerar exceção.

Funções Globais:
    - is_image_file(path): Verifica se o caminho corresponde a um arquivo de imagem
      com formato suportado (JPG, JPEG, PNG, WEBP, BMP, TIFF, TIF, GIF, ICO).
    - enable_drag_drop(tk_widget, callback): Registra o widget Tkinter para aceitar
      arquivos arrastados. O callback é chamado com assinatura:
          callback(files_list: list[str], drop_x: int|None, drop_y: int|None)
================================================================================
"""

import os
import platform

VALID_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    ".tiff", ".tif", ".gif", ".ico"
}


def is_image_file(path):
    """Verifica se o arquivo possui uma extensão de imagem suportada."""
    _, ext = os.path.splitext(path)
    return ext.lower() in VALID_EXTENSIONS


def enable_drag_drop(tk_widget, callback):
    """
    Habilita o recebimento de arquivos arrastados do Windows Explorer para o widget Tkinter.

    Usa tkinterdnd2 que integra nativamente com o event loop do Tkinter.
    O callback é chamado na thread principal do Tkinter com as coordenadas do drop.

    :param tk_widget: Instância de tk.Tk, tk.Toplevel ou qualquer widget Tkinter.
    :param callback:  Função chamada com assinatura (files_list, drop_x, drop_y).
    :returns: True se o suporte foi ativado, False caso contrário.
    """
    if platform.system() != "Windows":
        return False

    try:
        import tkinterdnd2 as tkdnd

        # Verifica se o widget já tem suporte a DnD (tkdnd.Tk ou tkdnd.Toplevel)
        # Se não, tenta registrar o widget para DnD
        if not hasattr(tk_widget, 'drop_target_register'):
            # Tenta obter a instância raiz tkdnd
            root = tk_widget.winfo_toplevel()
            if not hasattr(root, 'drop_target_register'):
                # A raiz não é um tkdnd.Tk, não podemos habilitar DnD facilmente
                # sem recriar a janela como tkdnd.Tk
                print("[drag_drop] Aviso: janela principal não é tkdnd.Tk, Drag & Drop limitado.")
                return False
            tk_widget = root

        def _on_drop(event):
            """Callback para evento de drop do tkinterdnd2."""
            try:
                # event.data contém a lista de arquivos como string Tcl
                # Formato Tcl list: {arquivo1} {arquivo2} ... ou arquivo1 arquivo2 ...
                data = event.data
                if not data:
                    return

                # Parse correto de lista Tcl usando o parser nativo do Tkinter
                # Isso preserva paths com espaços, acentos e caracteres especiais
                try:
                    # tk_widget é a raiz tkdnd.Tk, que tem o interpretador Tcl
                    file_list = tk_widget.tk.splitlist(data)
                except Exception:
                    # Fallback: tenta shlex se splitlist falhar
                    import shlex
                    try:
                        file_list = shlex.split(data)
                    except ValueError:
                        file_list = data.split()

                # Filtra apenas arquivos de imagem
                image_files = [f for f in file_list if isinstance(f, str) and is_image_file(f)]
                if image_files and callback:
                    # Coordenadas do drop relativas ao widget
                    drop_x = event.x_root - tk_widget.winfo_rootx()
                    drop_y = event.y_root - tk_widget.winfo_rooty()
                    callback(image_files, drop_x, drop_y)
            except Exception as err:
                print(f"Erro no callback de Drag & Drop: {err}")

        # Registra o widget como target de drop
        tk_widget.drop_target_register(tkdnd.DND_FILES)
        tk_widget.dnd_bind('<<Drop>>', _on_drop)

        return True

    except ImportError:
        print("[drag_drop] Aviso: tkinterdnd2 não instalado. Drag & Drop desativado.")
        return False
    except Exception as err:
        print(f"[drag_drop] Aviso: falha ao inicializar Drag & Drop ({err}).")
        return False
