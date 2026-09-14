"""
================================================================================
Módulo: exif_gui.py
Descrição: Interface gráfica para comparação e cópia de dados EXIF entre imagens.
================================================================================
"""

import os
from PIL import Image, ExifTags
import tkinter as tk
from tkinter import ttk, messagebox

from exif_core import _get_exif_data
from exif_copy import copy_selected_exif_data
from exif_layout import create_exif_popup
from exif_display import (
    create_exif_display,
    create_no_exif_message,
    enable_selection_controls,
    select_all_tags,
    deselect_all_tags,
    get_selected_tags,
)


def show_exif_comparison_popup(parent, viewers):
    """
    Abre um popup comparando os dados EXIF das imagens abertas nos visualizadores
    com funcionalidade de copiar dados EXIF entre imagens.

    Args:
        parent: Janela pai (tk.Tk ou tk.Toplevel)
        viewers: Lista de objetos ImageViewer (máximo 3)
    """
    # Filtra apenas visualizadores que têm imagem carregada
    valid_viewers = [v for v in viewers if v.pil_image and v.file_path]

    if not valid_viewers:
        messagebox.showinfo("Sem imagens", "Nenhuma imagem carregada para comparar dados EXIF.")
        return

    num_cols = len(valid_viewers)
    popup = create_exif_popup(parent, num_cols)

    # Área de conteúdo com scroll
    viewer_data = {}  # Armazena dados de cada viewer para uso posterior

    for idx, viewer in enumerate(valid_viewers):
        col_frame = tk.Frame(popup, bg="#09090b")
        col_frame.grid(row=1, column=idx, sticky="nsew", padx=2, pady=2)
        col_frame.rowconfigure(2, weight=1)  # Row 2 é o scrollable frame
        col_frame.columnconfigure(0, weight=1)

        # Título da coluna com nome do arquivo
        file_name = os.path.basename(viewer.file_path)
        title_frame = tk.Frame(col_frame, bg="#27272a", height=40)
        title_frame.grid(row=0, column=0, sticky="ew")
        title_frame.pack_propagate(False)

        tk.Label(
            title_frame,
            text=f"{viewer.title}: {file_name}",
            font=("Segoe UI", 10, "bold"),
            fg="#60a5fa",
            bg="#27272a"
        ).pack(side=tk.LEFT, padx=10, pady=8)

        # Frame de controle (radio buttons From/To)
        control_frame = tk.Frame(col_frame, bg="#18181b", height=60)
        control_frame.grid(row=1, column=0, sticky="ew", padx=4, pady=4)
        control_frame.pack_propagate(False)

        # Variável única para radio buttons (3 estados: None, "from", "to")
        role_var = tk.StringVar(value="")

        # Label "Origem/Destino"
        tk.Label(
            control_frame,
            text="Papel:",
            font=("Segoe UI", 9, "bold"),
            fg="#a5b4fc",
            bg="#18181b"
        ).pack(side=tk.LEFT, padx=(10, 5), pady=10)

        # Obtém dados EXIF para verificar se a imagem tem dados
        exif_data = _get_exif_data(viewer.file_path)
        has_exif = bool(exif_data)

        # Radio button "From" (Origem) - só habilitado se tem EXIF
        rb_from = tk.Radiobutton(
            control_frame,
            text="📤 Origem (From)",
            variable=role_var,
            value="from",
            font=("Segoe UI", 9),
            fg="#60a5fa" if has_exif else "#71717a",
            bg="#18181b",
            selectcolor="#09090b",
            activebackground="#18181b",
            activeforeground="#93c5fd" if has_exif else "#71717a",
            cursor="hand2" if has_exif else "arrow",
            state=tk.NORMAL if has_exif else tk.DISABLED
        )
        rb_from.pack(side=tk.LEFT, padx=5, pady=10)

        # Radio button "To" (Destino) - sempre habilitado
        rb_to = tk.Radiobutton(
            control_frame,
            text="📥 Destino (To)",
            variable=role_var,
            value="to",
            font=("Segoe UI", 9),
            fg="#fbbf24",
            bg="#18181b",
            selectcolor="#09090b",
            activebackground="#18181b",
            activeforeground="#fcd34d",
            cursor="hand2"
        )
        rb_to.pack(side=tk.LEFT, padx=5, pady=10)

        # Radio button "Nenhum" (oculto, para desmarcar)
        rb_none = tk.Radiobutton(
            control_frame,
            text="",
            variable=role_var,
            value="",
            font=("Segoe UI", 9),
            bg="#18181b",
            selectcolor="#09090b",
            activebackground="#18181b",
        )
        # Não faz pack - é apenas para permitir desmarcar programaticamente

        # Frame com scroll para os dados EXIF
        canvas = tk.Canvas(col_frame, bg="#09090b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(col_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#09090b")

        scrollable_frame.bind(
            "<Configure>",
            lambda e, c=canvas: c.configure(scrollregion=c.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=2, column=0, sticky="nsew")
        scrollbar.grid(row=2, column=1, sticky="ns")

        # Cria a exibição de dados EXIF usando o módulo exif_display
        if has_exif:
            tag_vars, tag_checkboxes, btn_select_all, btn_deselect_all = create_exif_display(
                scrollable_frame, exif_data
            )
        else:
            create_no_exif_message(scrollable_frame)
            tag_vars = {}
            tag_checkboxes = {}
            btn_select_all = tk.Button(state=tk.DISABLED)
            btn_deselect_all = tk.Button(state=tk.DISABLED)

        # Configura scroll com roda do mouse
        def _on_mousewheel(event, c=canvas):
            c.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e, c=canvas: c.bind_all("<MouseWheel>", lambda ev: _on_mousewheel(ev, c)))
        canvas.bind("<Leave>", lambda e, c=canvas: c.unbind_all("<MouseWheel>"))

        # Armazena dados do viewer
        viewer_data[idx] = {
            'viewer': viewer,
            'file_path': viewer.file_path,
            'exif_data': exif_data,
            'has_exif': has_exif,
            'role_var': role_var,
            'rb_from': rb_from,
            'rb_to': rb_to,
            'rb_none': rb_none,
            'tag_vars': tag_vars,
            'tag_checkboxes': tag_checkboxes,
            'btn_select_all': btn_select_all,
            'btn_deselect_all': btn_deselect_all,
            'scrollable_frame': scrollable_frame
        }

    # Botão "Copiar e Salvar" no rodapé
    footer_frame = tk.Frame(popup, bg="#18181b", height=60)
    footer_frame.grid(row=2, column=0, columnspan=num_cols, sticky="ew", padx=4, pady=4)
    footer_frame.pack_propagate(False)

    btn_copy_save = tk.Button(
        footer_frame,
        text="💾 Copiar e Salvar",
        font=("Segoe UI", 10, "bold"),
        bg="#16a34a",
        fg="white",
        activebackground="#15803d",
        activeforeground="white",
        relief=tk.FLAT,
        padx=20,
        pady=8,
        cursor="hand2",
        state=tk.DISABLED
    )
    btn_copy_save.pack(side=tk.RIGHT, padx=12, pady=10)

    # Label de status
    lbl_status = tk.Label(
        footer_frame,
        text="Selecione uma imagem como 'Origem (From)' para começar",
        font=("Segoe UI", 9),
        fg="#71717a",
        bg="#18181b"
    )
    lbl_status.pack(side=tk.LEFT, padx=12, pady=10)

    # --- Lógica de controle ---

    def update_ui_state():
        """Atualiza o estado da UI baseado nas seleções From/To"""
        from_idx = None
        to_indices = []

        for idx, data in viewer_data.items():
            role = data['role_var'].get()
            if role == "from":
                from_idx = idx
            elif role == "to":
                to_indices.append(idx)

        # Atualiza checkboxes e botões
        for idx, data in viewer_data.items():
            is_from = (idx == from_idx)

            # Habilita/desabilita checkboxes e botões select all
            # Só habilita se for a imagem From E tiver dados EXIF
            state = tk.NORMAL if (is_from and data['has_exif']) else tk.DISABLED
            enable_selection_controls(
                data['tag_checkboxes'],
                data['btn_select_all'],
                data['btn_deselect_all'],
                enabled=(is_from and data['has_exif'])
            )
            
            # Atualiza aparência dos radio buttons
            role = data['role_var'].get()
            if role == "from":
                data['rb_from'].config(fg="#60a5fa")
                data['rb_to'].config(fg="#71717a")
            elif role == "to":
                data['rb_to'].config(fg="#fbbf24")
                data['rb_from'].config(fg="#71717a")
            else:
                # Para imagens sem EXIF, o botão From fica desabilitado e cinza
                if not data['has_exif']:
                    data['rb_from'].config(fg="#71717a")
                    data['rb_to'].config(fg="#71717a")
                else:
                    data['rb_from'].config(fg="#71717a")
                    data['rb_to'].config(fg="#71717a")

        # Atualiza botão Copiar e Salvar
        has_selection = False
        if from_idx is not None:
            from_data = viewer_data[from_idx]
            for var in from_data['tag_vars'].values():
                if var.get():
                    has_selection = True
                    break

        can_copy = (from_idx is not None and len(to_indices) > 0 and has_selection)
        btn_copy_save.config(state=tk.NORMAL if can_copy else tk.DISABLED)

        # Atualiza status
        if from_idx is not None:
            from_name = os.path.basename(viewer_data[from_idx]['file_path'])
            if to_indices:
                to_names = [os.path.basename(viewer_data[i]['file_path']) for i in to_indices]
                lbl_status.config(text=f"Origem: {from_name} → Destino(s): {', '.join(to_names)}")
            else:
                lbl_status.config(text=f"Origem: {from_name} - Selecione uma imagem como Destino (To)")
        else:
            lbl_status.config(text="Selecione uma imagem como 'Origem (From)' para começar")

    def on_role_changed(selected_idx):
        """Callback quando o papel de uma imagem muda"""
        selected_role = viewer_data[selected_idx]['role_var'].get()

        # Se selecionou "From", desmarca From das outras
        if selected_role == "from":
            for idx, data in viewer_data.items():
                if idx != selected_idx and data['role_var'].get() == "from":
                    data['role_var'].set("")

        # Se só tem 2 imagens, gerencia automaticamente
        if num_cols == 2:
            other_idx = 1 if selected_idx == 0 else 0
            other_role = viewer_data[other_idx]['role_var'].get()

            if selected_role == "from" and other_role != "to":
                # Se escolheu From, a outra vira To automaticamente
                viewer_data[other_idx]['role_var'].set("to")
            elif selected_role == "to" and other_role != "from":
                # Se escolheu To, a outra vira From automaticamente (se tiver EXIF)
                if viewer_data[other_idx]['has_exif']:
                    viewer_data[other_idx]['role_var'].set("from")
                else:
                    # Se a outra não tem EXIF, não pode ser From, então limpa a seleção
                    viewer_data[selected_idx]['role_var'].set("")
            elif selected_role == "":
                # Se desmarcou, limpa a outra também se ela não tiver role oposto
                if other_role == "from" or other_role == "to":
                    viewer_data[other_idx]['role_var'].set("")
        # Se tem 3 imagens, não faz nada automático - usuário escolhe manualmente

        update_ui_state()

    def select_all_tags_callback(from_idx):
        """Seleciona todas as tags da imagem From"""
        data = viewer_data[from_idx]
        select_all_tags(data['tag_vars'])
        update_ui_state()

    def deselect_all_tags_callback(from_idx):
        """Desmarca todas as tags da imagem From"""
        data = viewer_data[from_idx]
        for var in data['tag_vars'].values():
            var.set(False)
        update_ui_state()

    # Conecta callbacks - usa trace na variável role_var
    for idx, data in viewer_data.items():
        data['role_var'].trace_add('write', lambda *args, i=idx: on_role_changed(i))
        data['btn_select_all'].config(command=lambda i=idx: select_all_tags_callback(i))
        data['btn_deselect_all'].config(command=lambda i=idx: deselect_all_tags_callback(i))

    btn_copy_save.config(command=lambda: copy_selected_exif_data(parent, popup, viewer_data))

    # Inicializa o estado da UI (radio buttons começam desmarcados = "")
    update_ui_state()

    # Centraliza o popup na janela pai
    popup.transient(parent)
    popup.grab_set()
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")