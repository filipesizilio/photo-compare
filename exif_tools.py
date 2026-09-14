
import os
from PIL import Image, ExifTags
import tkinter as tk
from tkinter import ttk, messagebox

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
    
    # Cria a janela popup
    popup = tk.Toplevel(parent)
    popup.title("Comparação de Dados EXIF")
    popup.geometry("1400x800")
    popup.minsize(1000, 600)
    popup.configure(bg="#0f0f11")
    
    # Tenta definir o ícone
    try:
        icon_ico = os.path.join(os.path.dirname(__file__), "assets", "icon.ico")
        if os.path.exists(icon_ico):
            popup.iconbitmap(icon_ico)
    except Exception:
        pass
    
    # Configura o grid para colunas proporcionais
    num_cols = len(valid_viewers)
    for i in range(num_cols):
        popup.columnconfigure(i, weight=1, uniform="exif_cols")
    popup.rowconfigure(1, weight=1)
    
    # Cabeçalho
    header_frame = tk.Frame(popup, bg="#18181b", height=50)
    header_frame.grid(row=0, column=0, columnspan=num_cols, sticky="ew", padx=4, pady=4)
    header_frame.pack_propagate(False)
    
    tk.Label(
        header_frame,
        text="Comparação de Metadados EXIF",
        font=("Segoe UI", 12, "bold"),
        fg="#f4f4f5",
        bg="#18181b"
    ).pack(side=tk.LEFT, padx=12, pady=12)
    
    # Botão fechar
    tk.Button(
        header_frame,
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
        command=popup.destroy
    ).pack(side=tk.RIGHT, padx=12, pady=8)
    
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
        
        # Armazena checkboxes e variáveis para cada tag
        tag_checkboxes = {}
        tag_vars = {}
        
        # Frame para botão "Selecionar Tudo"
        select_all_frame = tk.Frame(scrollable_frame, bg="#09090b")
        select_all_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 4))
        
        btn_select_all = tk.Button(
            select_all_frame,
            text="☑ Selecionar Tudo",
            font=("Segoe UI", 8, "bold"),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        btn_select_all.pack(side=tk.LEFT, padx=(0, 8))
        
        btn_deselect_all = tk.Button(
            select_all_frame,
            text="☐ Desmarcar Tudo",
            font=("Segoe UI", 8),
            bg="#3f3f46",
            fg="#f4f4f5",
            activebackground="#52525b",
            activeforeground="white",
            relief=tk.FLAT,
            padx=8,
            pady=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        btn_deselect_all.pack(side=tk.LEFT)
        
        # Exibe os dados EXIF com checkboxes (ou mensagem se não tiver)
        if has_exif:
            # Agrupa por categoria
            categories = {
                "Imagem": ["ImageWidth", "ImageLength", "BitsPerSample", "Compression", "PhotometricInterpretation", "Orientation", "SamplesPerPixel", "PlanarConfiguration", "YCbCrSubSampling", "YCbCrPositioning", "XResolution", "YResolution", "ResolutionUnit"],
                "Câmera": ["Make", "Model", "Software", "DateTime", "Artist", "Copyright"],
                "Exposição": ["ExposureTime", "FNumber", "ExposureProgram", "SpectralSensitivity", "ISOSpeedRatings", "OECF", "ShutterSpeedValue", "ApertureValue", "BrightnessValue", "ExposureBiasValue", "MaxApertureValue", "SubjectDistance", "MeteringMode", "LightSource", "Flash", "FocalLength", "SubjectArea", "MakerNote", "UserComment", "SubsecTime", "SubsecTimeOriginal", "SubsecTimeDigitized"],
                "Data/Hora": ["DateTimeOriginal", "DateTimeDigitized", "OffsetTime", "OffsetTimeOriginal", "OffsetTimeDigitized"],
                "GPS": ["GPSVersionID", "GPSLatitudeRef", "GPSLatitude", "GPSLongitudeRef", "GPSLongitude", "GPSAltitudeRef", "GPSAltitude", "GPSTimeStamp", "GPSSatellites", "GPSStatus", "GPSMeasureMode", "GPSDOP", "GPSSpeedRef", "GPSSpeed", "GPSTrackRef", "GPSTrack", "GPSImgDirectionRef", "GPSImgDirection", "GPSMapDatum", "GPSDestLatitudeRef", "GPSDestLatitude", "GPSDestLongitudeRef", "GPSDestLongitude", "GPSDestBearingRef", "GPSDestBearing", "GPSDestDistanceRef", "GPSDestDistance", "GPSProcessingMethod", "GPSAreaInformation", "GPSDateStamp", "GPSDifferential"],
                "Outros": []
            }
            
            # Adiciona tags não categorizadas em "Outros"
            categorized_tags = set()
            for cat_tags in categories.values():
                categorized_tags.update(cat_tags)
            
            for tag in exif_data:
                if tag not in categorized_tags:
                    categories["Outros"].append(tag)
            
            # Remove categorias vazias
            categories = {k: v for k, v in categories.items() if v}
            
            row = 1  # Começa na linha 1 (linha 0 é o botão Selecionar Tudo)
            for category, tags in categories.items():
                # Cabeçalho da categoria
                cat_label = tk.Label(
                    scrollable_frame,
                    text=category,
                    font=("Segoe UI", 9, "bold"),
                    fg="#a5b4fc",
                    bg="#09090b",
                    anchor="w"
                )
                cat_label.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 2))
                row += 1
                
                # Separador
                sep = tk.Frame(scrollable_frame, bg="#27272a", height=1)
                sep.grid(row=row, column=0, columnspan=3, sticky="ew", padx=8)
                row += 1
                
                for tag in tags:
                    if tag in exif_data:
                        value = exif_data[tag]
                        # Formata o valor para exibição
                        if isinstance(value, bytes):
                            try:
                                value = value.decode('utf-8', errors='replace')
                            except:
                                value = str(value)
                        elif isinstance(value, tuple):
                            value = str(value)
                        
                        # Limita o tamanho do valor exibido
                        value_str = str(value)
                        if len(value_str) > 200:
                            value_str = value_str[:200] + "..."
                        
                        # Checkbox para seleção
                        var = tk.BooleanVar(value=False)
                        tag_vars[tag] = var
                        
                        cb = tk.Checkbutton(
                            scrollable_frame,
                            variable=var,
                            font=("Segoe UI", 8),
                            fg="#e4e4e7",
                            bg="#09090b",
                            selectcolor="#18181b",
                            activebackground="#09090b",
                            activeforeground="#e4e4e7",
                            cursor="hand2",
                            state=tk.DISABLED
                        )
                        cb.grid(row=row, column=0, sticky="w", padx=(12, 4), pady=1)
                        tag_checkboxes[tag] = cb
                        
                        # Label da tag
                        tag_label = tk.Label(
                            scrollable_frame,
                            text=tag,
                            font=("Segoe UI", 8),
                            fg="#71717a",
                            bg="#09090b",
                            anchor="w",
                            justify="left"
                        )
                        tag_label.grid(row=row, column=1, sticky="nw", padx=(0, 4), pady=1)
                        
                        # Label do valor
                        val_label = tk.Label(
                            scrollable_frame,
                            text=value_str,
                            font=("Segoe UI", 8),
                            fg="#e4e4e7",
                            bg="#09090b",
                            anchor="w",
                            justify="left",
                            wraplength=300
                        )
                        val_label.grid(row=row, column=2, sticky="nw", padx=(0, 12), pady=1)
                        row += 1
        else:
            # Imagem sem dados EXIF - mostra mensagem
            tk.Label(
                scrollable_frame,
                text="Nenhum dado EXIF encontrado nesta imagem.\n\nEsta imagem pode receber dados EXIF de outra imagem\nselecionando 'Destino (To)'.",
                font=("Segoe UI", 9),
                fg="#71717a",
                bg="#09090b",
                justify=tk.CENTER
            ).grid(row=1, column=0, columnspan=3, padx=20, pady=40, sticky="nsew")
            # Configura a linha e coluna para expandir
            scrollable_frame.rowconfigure(1, weight=1)
            scrollable_frame.columnconfigure(0, weight=1)
        
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
            for cb in data['tag_checkboxes'].values():
                cb.config(state=state)
            data['btn_select_all'].config(state=state)
            data['btn_deselect_all'].config(state=state)
            
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
    
    def select_all_tags(from_idx):
        """Seleciona todas as tags da imagem From"""
        data = viewer_data[from_idx]
        for var in data['tag_vars'].values():
            var.set(True)
        update_ui_state()
    
    def deselect_all_tags(from_idx):
        """Desmarca todas as tags da imagem From"""
        data = viewer_data[from_idx]
        for var in data['tag_vars'].values():
            var.set(False)
        update_ui_state()
    
    def copy_exif_data():
        """Copia os dados EXIF selecionados da imagem From para a(s) imagem(ns) To"""
        from_idx = None
        to_indices = []
        
        for idx, data in viewer_data.items():
            role = data['role_var'].get()
            if role == "from":
                from_idx = idx
            elif role == "to":
                to_indices.append(idx)
        
        if from_idx is None or not to_indices:
            messagebox.showwarning("Aviso", "Selecione uma imagem como Origem (From) e pelo menos uma como Destino (To).")
            return
        
        from_data = viewer_data[from_idx]
        selected_tags = [tag for tag, var in from_data['tag_vars'].items() if var.get()]
        
        if not selected_tags:
            messagebox.showwarning("Aviso", "Selecione pelo menos um dado EXIF para copiar.")
            return
        
        from_path = from_data['file_path']
        
        # Confirmação
        to_names = [os.path.basename(viewer_data[i]['file_path']) for i in to_indices]
        confirm = messagebox.askyesno(
            "Confirmar Cópia",
            f"Copiar {len(selected_tags)} dado(s) EXIF de:\n"
            f"  {os.path.basename(from_path)} (Origem)\n\n"
            f"Para:\n" + "\n".join(f"  {name} (Destino)" for name in to_names) + "\n\n"
            f"Os dados EXIF existentes nas imagens de destino serão preservados,\n"
            f"apenas os dados selecionados serão atualizados.\n\n"
            f"Continuar?"
        )
        
        if not confirm:
            return
        
        # Carrega EXIF da origem
        try:
            import piexif
            with Image.open(from_path) as img:
                exif_bytes = img.info.get('exif')
                if not exif_bytes:
                    messagebox.showerror("Erro", "Imagem de origem não possui dados EXIF.")
                    return
                from_exif_dict = piexif.load(exif_bytes)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao ler EXIF da imagem de origem:\n{e}")
            return
        
        # Mapeia nomes de tags amigáveis para IDs do piexif
        tag_to_ifd = {}
        for ifd_name in ["0th", "Exif", "GPS", "Interop", "1st"]:
            if ifd_name in from_exif_dict:
                for tag_id, value in from_exif_dict[ifd_name].items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    tag_to_ifd[tag_name] = (ifd_name, tag_id, value)
        
        # Copia para cada destino
        success_count = 0
        for to_idx in to_indices:
            to_path = viewer_data[to_idx]['file_path']
            try:
                with Image.open(to_path) as img:
                    exif_bytes = img.info.get('exif')
                    if exif_bytes:
                        to_exif_dict = piexif.load(exif_bytes)
                    else:
                        to_exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}, "thumbnail": None}
                    
                    # Copia apenas as tags selecionadas
                    copied = 0
                    for tag in selected_tags:
                        if tag in tag_to_ifd:
                            ifd_name, tag_id, value = tag_to_ifd[tag]
                            to_exif_dict[ifd_name][tag_id] = value
                            copied += 1
                    
                    if copied > 0:
                        # Salva a imagem com EXIF atualizado
                        exif_bytes = piexif.dump(to_exif_dict)
                        img.save(to_path, exif=exif_bytes)
                        success_count += 1
                        
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar EXIF em {os.path.basename(to_path)}:\n{e}")
                return
        
        if success_count > 0:
            messagebox.showinfo(
                "Sucesso",
                f"Dados EXIF copiados com sucesso!\n"
                f"{len(selected_tags)} tag(s) copiada(s) para {success_count} imagem(ns)."
            )
            # Atualiza a exibição recarregando os dados
            # Para simplificar, apenas fecha o popup - o usuário pode reabrir
            popup.destroy()
        else:
            messagebox.showwarning("Aviso", "Nenhum dado foi copiado.")
    
    # Conecta callbacks - usa trace na variável role_var
    for idx, data in viewer_data.items():
        data['role_var'].trace_add('write', lambda *args, i=idx: on_role_changed(i))
        data['btn_select_all'].config(command=lambda i=idx: select_all_tags(i))
        data['btn_deselect_all'].config(command=lambda i=idx: deselect_all_tags(i))
    
    btn_copy_save.config(command=copy_exif_data)
    
    # Inicializa o estado da UI (radio buttons começam desmarcados = "")
    update_ui_state()
    
    # Centraliza o popup na janela pai
    popup.transient(parent)
    popup.grab_set()
    parent.update_idletasks()
    x = parent.winfo_x() + (parent.winfo_width() // 2) - (popup.winfo_width() // 2)
    y = parent.winfo_y() + (parent.winfo_height() // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"+{x}+{y}")


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
            exif_data = img_original.info.get('exif') # Obtém os dados EXIF brutos

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

def test():
    input_image_path  = "hcluts/Hald CLUT VSCO A5.png"
    output_image_path = "hcluts/Hald CLUT VSCO A5 - output.png"
    
    exif_data = _get_exif_data(input_image_path)
    
    print(f"Dados EXIF da imagem: {input_image_path}")
    for key, value in exif_data.items():
        print(f"{key}: {value}")


    # print("\nVerificando dados GPS...")
    # if "GPSInfo" in exif_data:
    #     gmaps_link = _gps_to_gmaps(exif_data["GPSInfo"])
    #     print(f"Link do Google Maps: {gmaps_link}")
    # else:
    #     print("Nenhum dado GPS encontrado.")
    
    # print("\nAdicionando dados de localização ao EXIF...")
    # _write_gps_to_exif(input_image_path, output_image_path, 37.7749, -122.4194, 55)
    # exif_data_output = _get_exif_data(output_image_path)
    # gmaps_link_output = _gps_to_gmaps(exif_data_output["GPSInfo"])
    # print(f"Link do Google Maps da nova localização: {gmaps_link_output}")

    input("\nTodos os dados EXIF da imagem serão apagados. Pressione Enter para continuar...")
    _clean_exif_data(input_image_path, output_image_path)

def main():
    print("Este módulo é parte integrante do script principal ict2hclut.py.\n")
    print("Funções disponíveis:")
    print("  1. _transfer_exif_data")
    print("  2. _clean_exif_data")
    print("  3. _get_exif_data")
    print("  4. _gps_to_gmaps")
    print("  5. _write_gps_to_exif")

    # Executando em modo de teste -> comentar as linhas abaixo se for usar após testes
    print("\nExecutando teste de funcionalidade...")
    test()
    
    
if __name__ == "__main__":
    main()