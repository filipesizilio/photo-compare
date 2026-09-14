"""Cópia seletiva de dados EXIF entre imagens."""

import os
from tkinter import messagebox
from PIL import Image, ExifTags

from exif_display import get_selected_tags


def copy_selected_exif_data(parent, popup, viewer_data):
    """Copia os dados selecionados da imagem From para as imagens To."""
    from_idx = None
    to_indices = []

    for idx, data in viewer_data.items():
        role = data['role_var'].get()
        if role == "from":
            from_idx = idx
        elif role == "to":
            to_indices.append(idx)

    if from_idx is None or not to_indices:
        messagebox.showwarning(
            "Aviso",
            "Selecione uma imagem como Origem (From) e pelo menos uma como Destino (To).",
        )
        return

    from_data = viewer_data[from_idx]
    selected_tags = get_selected_tags(from_data['tag_vars'])
    if not selected_tags:
        messagebox.showwarning("Aviso", "Selecione pelo menos um dado EXIF para copiar.")
        return

    from_path = from_data['file_path']
    to_names = [os.path.basename(viewer_data[i]['file_path']) for i in to_indices]
    confirm = messagebox.askyesno(
        "Confirmar Cópia",
        f"Copiar {len(selected_tags)} dado(s) EXIF de:\n"
        f"  {os.path.basename(from_path)} (Origem)\n\n"
        f"Para:\n" + "\n".join(f"  {name} (Destino)" for name in to_names) + "\n\n"
        "Os dados EXIF existentes nas imagens de destino serão preservados,\n"
        "apenas os dados selecionados serão atualizados.\n\n"
        "Continuar?",
    )
    if not confirm:
        return

    try:
        import piexif

        with Image.open(from_path) as image:
            exif_bytes = image.info.get('exif')
            if not exif_bytes:
                messagebox.showerror("Erro", "Imagem de origem não possui dados EXIF.")
                return
            from_exif_dict = piexif.load(exif_bytes)
    except Exception as error:
        messagebox.showerror("Erro", f"Erro ao ler EXIF da imagem de origem:\n{error}")
        return

    tag_to_ifd = {}
    for ifd_name in ["0th", "Exif", "GPS", "Interop", "1st"]:
        for tag_id, value in from_exif_dict.get(ifd_name, {}).items():
            tag_name = ExifTags.TAGS.get(tag_id, tag_id)
            tag_to_ifd[tag_name] = (ifd_name, tag_id, value)

    success_count = 0
    for to_idx in to_indices:
        to_path = viewer_data[to_idx]['file_path']
        try:
            with Image.open(to_path) as image:
                exif_bytes = image.info.get('exif')
                if exif_bytes:
                    to_exif_dict = piexif.load(exif_bytes)
                else:
                    to_exif_dict = {
                        "0th": {}, "Exif": {}, "GPS": {},
                        "Interop": {}, "1st": {}, "thumbnail": None,
                    }

                copied = 0
                for tag in selected_tags:
                    if tag in tag_to_ifd:
                        ifd_name, tag_id, value = tag_to_ifd[tag]
                        to_exif_dict[ifd_name][tag_id] = value
                        copied += 1

                if copied > 0:
                    image.save(to_path, exif=piexif.dump(to_exif_dict))
                    success_count += 1
        except Exception as error:
            messagebox.showerror(
                "Erro",
                f"Erro ao salvar EXIF em {os.path.basename(to_path)}:\n{error}",
            )
            return

    if success_count > 0:
        messagebox.showinfo(
            "Sucesso",
            f"Dados EXIF copiados com sucesso!\n"
            f"{len(selected_tags)} tag(s) copiada(s) para {success_count} imagem(ns).",
        )
        popup.destroy()
    else:
        messagebox.showwarning("Aviso", "Nenhum dado foi copiado.")
