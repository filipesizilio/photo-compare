"""Layout comum da janela de comparação EXIF."""

import os
import tkinter as tk


def create_exif_popup(parent, column_count):
    """Cria a janela, cabeçalho e botão de fechamento do popup EXIF."""
    popup = tk.Toplevel(parent)
    popup.title("Comparação de Dados EXIF")
    popup.geometry("1400x800")
    popup.minsize(1000, 600)
    popup.configure(bg="#0f0f11")

    try:
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_path):
            popup.iconbitmap(icon_path)
    except Exception:
        pass

    for column in range(column_count):
        popup.columnconfigure(column, weight=1, uniform="exif_cols")
    popup.rowconfigure(1, weight=1)

    header = tk.Frame(popup, bg="#18181b", height=50)
    header.grid(row=0, column=0, columnspan=column_count, sticky="ew", padx=4, pady=4)
    header.pack_propagate(False)

    tk.Label(
        header,
        text="Comparação de Metadados EXIF",
        font=("Segoe UI", 12, "bold"),
        fg="#f4f4f5",
        bg="#18181b",
    ).pack(side=tk.LEFT, padx=12, pady=12)

    tk.Button(
        header,
        text="✕ Fechar",
        font=("Segoe UI", 9),
        bg="#7f1d1d",
        fg="white",
        activebackground="#991b1b",
        activeforeground="white",
        relief=tk.FLAT,
        padx=12,
        pady=4,
        cursor="hand2",
        command=popup.destroy,
    ).pack(side=tk.RIGHT, padx=12, pady=8)

    return popup
