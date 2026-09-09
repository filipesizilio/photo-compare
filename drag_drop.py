"""
Módulo de suporte a Arraste e Solte (Drag & Drop) nativo no Windows para Tkinter.
Utiliza a API Win32 (shell32 e user32 via ctypes) sem dependências externas compiladas.
"""

import os
import platform
import sys
import ctypes
from ctypes import wintypes

VALID_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp",
    ".tiff", ".tif", ".gif", ".ico"
}

# Referência global para evitar coleta de lixo dos ponteiros WNDPROC
_registered_hooks = {}


def is_image_file(path):
    """Verifica se o arquivo possui uma extensão de imagem suportada."""
    _, ext = os.path.splitext(path)
    return ext.lower() in VALID_EXTENSIONS


def enable_drag_drop(tk_widget, callback):
    """
    Habilita o recebimento de arquivos arrastados do Windows Explorer para o widget Tkinter.
    
    :param tk_widget: Instância de tk.Tk, tk.Toplevel, tk.Frame ou tk.Canvas
    :param callback: Função chamada com assinatura (files_list, drop_x, drop_y)
    """
    if platform.system() != "Windows":
        return False

    tk_widget.update_idletasks()
    hwnd = tk_widget.winfo_id()

    # Tipos e constantes Win32
    WM_DROPFILES = 0x0233
    GWLP_WNDPROC = -4

    is_64bit = platform.architecture()[0] == "64bit"

    if is_64bit:
        SetWindowLongPtr = ctypes.windll.user32.SetWindowLongPtrW
        SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_void_p]
        SetWindowLongPtr.restype = ctypes.c_void_p

        GetWindowLongPtr = ctypes.windll.user32.GetWindowLongPtrW
        GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
        GetWindowLongPtr.restype = ctypes.c_void_p

        WNDPROC = ctypes.WINFUNCTYPE(
            ctypes.c_ssize_t,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM
        )
    else:
        SetWindowLongPtr = ctypes.windll.user32.SetWindowLongW
        SetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.LONG]
        SetWindowLongPtr.restype = wintypes.LONG

        GetWindowLongPtr = ctypes.windll.user32.GetWindowLongW
        GetWindowLongPtr.argtypes = [wintypes.HWND, ctypes.c_int]
        GetWindowLongPtr.restype = wintypes.LONG

        WNDPROC = ctypes.WINFUNCTYPE(
            wintypes.LPARAM,
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM
        )

    CallWindowProc = ctypes.windll.user32.CallWindowProcW
    CallWindowProc.restype = ctypes.c_ssize_t if is_64bit else wintypes.LPARAM

    DragQueryFileW = ctypes.windll.shell32.DragQueryFileW
    DragQueryFileW.restype = wintypes.UINT
    DragQueryFileW.argtypes = [wintypes.HANDLE, wintypes.UINT, wintypes.LPWSTR, wintypes.UINT]

    DragQueryPoint = ctypes.windll.shell32.DragQueryPoint
    DragQueryPoint.restype = wintypes.BOOL
    DragQueryPoint.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.POINT)]

    DragFinish = ctypes.windll.shell32.DragFinish
    DragFinish.restype = None
    DragFinish.argtypes = [wintypes.HANDLE]

    DragAcceptFiles = ctypes.windll.shell32.DragAcceptFiles
    DragAcceptFiles.restype = None
    DragAcceptFiles.argtypes = [wintypes.HWND, wintypes.BOOL]

    # Ativa aceitação de arquivos na janela
    DragAcceptFiles(hwnd, True)

    old_wndproc = GetWindowLongPtr(hwnd, GWLP_WNDPROC)

    def wndproc(h, msg, wp, lp):
        if msg == WM_DROPFILES:
            hDrop = wintypes.HANDLE(wp)

            # Extrai coordenadas do drop
            pt = wintypes.POINT()
            has_pt = DragQueryPoint(hDrop, ctypes.byref(pt))
            drop_x = pt.x if has_pt else None
            drop_y = pt.y if has_pt else None

            # Extrai os caminhos dos arquivos com suporte completo a Unicode
            count = DragQueryFileW(hDrop, 0xFFFFFFFF, None, 0)
            file_paths = []
            for i in range(count):
                length = DragQueryFileW(hDrop, i, None, 0)
                buf = ctypes.create_unicode_buffer(length + 1)
                DragQueryFileW(hDrop, i, buf, length + 1)
                file_paths.append(buf.value)

            DragFinish(hDrop)

            if callback:
                try:
                    callback(file_paths, drop_x, drop_y)
                except Exception as err:
                    print(f"Erro no callback de Drag & Drop: {err}")

            return 0

        return CallWindowProc(ctypes.c_void_p(old_wndproc), h, msg, wp, lp)

    proc_ref = WNDPROC(wndproc)
    SetWindowLongPtr(hwnd, GWLP_WNDPROC, ctypes.cast(proc_ref, ctypes.c_void_p).value)

    # Armazena referências para prevenir descarte pelo garbage collector
    _registered_hooks[hwnd] = {
        "proc": proc_ref,
        "old_wndproc": old_wndproc,
        "hwnd": hwnd,
        "SetWindowLongPtr": SetWindowLongPtr,
        "DragAcceptFiles": DragAcceptFiles
    }

    # Desvincula quando o widget for destruído
    def _cleanup(event=None):
        if hwnd in _registered_hooks:
            info = _registered_hooks.pop(hwnd)
            try:
                info["SetWindowLongPtr"](hwnd, GWLP_WNDPROC, info["old_wndproc"])
                info["DragAcceptFiles"](hwnd, False)
            except Exception:
                pass

    tk_widget.bind("<Destroy>", _cleanup, add="+")
    return True

