"""
================================================================================
Módulo: exif_popup.py
Descrição: Interface gráfica para comparação e cópia de dados EXIF entre imagens.
================================================================================
"""

import os
from PIL import Image, ExifTags
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

from exif_core import _get_exif_data
from exif_copy import copy_selected_exif_data
from exif_popup_layout import create_exif_popup
from exif_tags_display import (
    create_exif_display,
    create_no_exif_message,
    enable_selection_controls,
    select_all_tags,
    deselect_all_tags,
    get_selected_tags,
)
from app_config import (
    CORNER_RADIUS,
    COLOR_TOOLBAR_BG,
    COLOR_VIEWER_BG,
    COLOR_VIEWER_HEADER,
    COLOR_VIEWER_TITLE,
    COLOR_TEXT_MUTED,
    COLOR_SYNC_LOCKED_FG,
    COLOR_SYNC_LOCKED_HOVER,
    COLOR_PRIMARY_TEXT,
    get_accent_color_for_title,
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
        accent = getattr(viewer, "accent_color", None) or get_accent_color_for_title(viewer.title)
        col_frame = ctk.CTkFrame(
            popup,
            fg_color=("gray95", "#09090b"),
            corner_radius=CORNER_RADIUS,
            border_width=4,
            border_color=accent,
        )
        col_frame.grid(row=1, column=idx, sticky="nsew", padx=4, pady=4)
        col_frame.rowconfigure(2, weight=1)  # Row 2 é o scrollable frame
        col_frame.columnconfigure(0, weight=1)

        # Título da coluna com nome do arquivo
        file_name = os.path.basename(viewer.file_path)
        title_frame = ctk.CTkFrame(
            col_frame,
            fg_color=COLOR_VIEWER_HEADER,
            corner_radius=CORNER_RADIUS,
            height=40
        )
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=7, pady=(7, 2))
        title_frame.pack_propagate(False)

        ctk.CTkLabel(
            title_frame,
            text=f"{viewer.title}: {file_name}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=accent
        ).pack(side=tk.LEFT, padx=10, pady=8)

        # Frame de controle (radio buttons From/To)
        control_frame = ctk.CTkFrame(
            col_frame,
            fg_color=COLOR_VIEWER_BG,
            corner_radius=CORNER_RADIUS,
            height=54
        )
        control_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=7, pady=2)
        control_frame.pack_propagate(False)

        # Variável única para radio buttons (3 estados: None, "from", "to")
        role_var = tk.StringVar(value="")

        # Label "Papel:"
        ctk.CTkLabel(
            control_frame,
            text="Papel:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=("#4338ca", "#a5b4fc")
        ).pack(side=tk.LEFT, padx=(10, 5), pady=8)

        # Obtém dados EXIF para verificar se a imagem tem dados
        exif_data = _get_exif_data(viewer.file_path)
        has_exif = bool(exif_data)

        # Radio button "From" (Origem) - só habilitado se tem EXIF
        rb_from = ctk.CTkRadioButton(
            control_frame,
            text="📤 Origem (From)",
            variable=role_var,
            value="from",
            font=ctk.CTkFont(size=11),
            text_color=("#2563eb", "#60a5fa") if has_exif else "gray50",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            state="normal" if has_exif else "disabled"
        )
        rb_from.pack(side=tk.LEFT, padx=5, pady=8)

        # Radio button "To" (Destino) - sempre habilitado
        rb_to = ctk.CTkRadioButton(
            control_frame,
            text="📥 Destino (To)",
            variable=role_var,
            value="to",
            font=ctk.CTkFont(size=11),
            text_color=("#d97706", "#fbbf24"),
            fg_color="#d97706",
            hover_color="#b45309"
        )
        rb_to.pack(side=tk.LEFT, padx=5, pady=8)

        # Radio button "Nenhum" (oculto, para desmarcar)
        rb_none = tk.Radiobutton(
            control_frame,
            text="",
            variable=role_var,
            value="",
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

        canvas.grid(row=2, column=0, sticky="nsew", padx=(7, 0), pady=(2, 7))
        scrollbar.grid(row=2, column=1, sticky="ns", padx=(0, 7), pady=(2, 7))

        # Cria a exibição de dados EXIF usando o módulo exif_tags_display
        if has_exif:
            tag_vars, tag_checkboxes, btn_select_all, btn_deselect_all = create_exif_display(
                scrollable_frame, exif_data
            )
        else:
            create_no_exif_message(scrollable_frame)
            tag_vars = {}
            tag_checkboxes = {}
            btn_select_all = ctk.CTkButton(col_frame, text="", state="disabled")
            btn_deselect_all = ctk.CTkButton(col_frame, text="", state="disabled")

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
    footer_frame = ctk.CTkFrame(
        popup,
        fg_color=COLOR_TOOLBAR_BG,
        corner_radius=0,
        height=54
    )
    footer_frame.grid(row=2, column=0, columnspan=num_cols, sticky="ew", padx=4, pady=4)
    footer_frame.pack_propagate(False)

    btn_copy_save = ctk.CTkButton(
        footer_frame,
        text="💾 Copiar e Salvar",
        font=ctk.CTkFont(size=12, weight="bold"),
        fg_color=COLOR_SYNC_LOCKED_FG,
        hover_color=COLOR_SYNC_LOCKED_HOVER,
        text_color=COLOR_PRIMARY_TEXT,
        width=150,
        height=36,
        corner_radius=CORNER_RADIUS,
        state="disabled"
    )
    btn_copy_save.pack(side=tk.RIGHT, padx=12, pady=9)

    # Label de status
    lbl_status = ctk.CTkLabel(
        footer_frame,
        text="Selecione uma imagem como 'Origem (From)' para começar",
        font=ctk.CTkFont(size=11),
        text_color=COLOR_TEXT_MUTED
    )
    lbl_status.pack(side=tk.LEFT, padx=12, pady=9)

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
                data['rb_from'].configure(text_color=("#2563eb", "#60a5fa"))
                data['rb_to'].configure(text_color="gray50")
            elif role == "to":
                data['rb_to'].configure(text_color=("#d97706", "#fbbf24"))
                data['rb_from'].configure(text_color="gray50")
            else:
                data['rb_from'].configure(text_color=("#2563eb", "#60a5fa") if data['has_exif'] else "gray50")
                data['rb_to'].configure(text_color=("#d97706", "#fbbf24"))

        # Atualiza botão Copiar e Salvar
        has_selection = False
        if from_idx is not None:
            from_data = viewer_data[from_idx]
            for var in from_data['tag_vars'].values():
                if var.get():
                    has_selection = True
                    break

        can_copy = (from_idx is not None and len(to_indices) > 0 and has_selection)
        btn_copy_save.configure(state="normal" if can_copy else "disabled")

        # Atualiza status
        if from_idx is not None:
            from_name = os.path.basename(viewer_data[from_idx]['file_path'])
            if to_indices:
                to_names = [os.path.basename(viewer_data[i]['file_path']) for i in to_indices]
                lbl_status.configure(text=f"Origem: {from_name} → Destino(s): {', '.join(to_names)}")
            else:
                lbl_status.configure(text=f"Origem: {from_name} - Selecione uma imagem como Destino (To)")
        else:
            lbl_status.configure(text="Selecione uma imagem como 'Origem (From)' para começar")

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
        try:
            data['btn_select_all'].configure(command=lambda i=idx: select_all_tags_callback(i))
            data['btn_deselect_all'].configure(command=lambda i=idx: deselect_all_tags_callback(i))
        except Exception:
            data['btn_select_all'].config(command=lambda i=idx: select_all_tags_callback(i))
            data['btn_deselect_all'].config(command=lambda i=idx: deselect_all_tags_callback(i))

    btn_copy_save.configure(command=lambda: copy_selected_exif_data(parent, popup, viewer_data))

    # Inicializa o estado da UI (radio buttons começam desmarcados = "")
    update_ui_state()

    # Centraliza o popup na janela pai
    popup.transient(parent)
    popup.grab_set()
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")