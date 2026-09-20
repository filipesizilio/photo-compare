"""
================================================================================
Módulo: ui_tooltip.py
Descrição: Helper de tooltip flutuante com delay e auto-descarte para widgets.
================================================================================
"""

import tkinter as tk


def add_tooltip(widget, text, delay=400):
    """Helper de tooltip com delay e descarte automático ao sair ou clicar."""
    tip = {"win": None, "after_id": None}

    def show(_event=None):
        def _create():
            try:
                win = tk.Toplevel(widget)
                win.overrideredirect(True)
                win.attributes("-topmost", True)
                label = tk.Label(
                    win, text=text, background="#2b2b2b", foreground="white",
                    padx=8, pady=4, borderwidth=0, font=("Segoe UI", 9)
                )
                label.pack()
                x = widget.winfo_rootx() + 10
                y = widget.winfo_rooty() + widget.winfo_height() + 6
                win.geometry(f"+{x}+{y}")
                tip["win"] = win
            except Exception:
                pass
        tip["after_id"] = widget.after(delay, _create)

    def hide(_event=None):
        if tip["after_id"]:
            try:
                widget.after_cancel(tip["after_id"])
            except Exception:
                pass
            tip["after_id"] = None
        if tip["win"]:
            try:
                tip["win"].destroy()
            except Exception:
                pass
            tip["win"] = None

    try:
        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)
        widget.bind("<Button-1>", hide)
    except NotImplementedError:
        # Widgets compostos do CustomTkinter (como CTkSegmentedButton) não implementam bind() no container
        # Vincula nos botões internos se disponíveis
        buttons = getattr(widget, "_buttons_dict", {}).values()
        for btn in buttons:
            try:
                btn.bind("<Enter>", show)
                btn.bind("<Leave>", hide)
                btn.bind("<Button-1>", hide)
            except Exception:
                pass

