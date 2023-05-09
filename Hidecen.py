import tkinter as tk
from tkinter import filedialog, Tk, Listbox, Label, Button
import numpy as np
from PIL import ImageTk,Image
from anonfile import AnonFile
from pathlib import Path
import re,struct,os
def encode_file():
    anon = AnonFile()
    error = False
    for filepath in filedialog.askopenfilenames():
        filename = os.path.basename(filepath)
        if os.path.exists(f"{filename}_links.txt"):
            print(f"Error: File {filename} has already been uploaded.")
            error = True
            continue
        with open(filepath, "rb") as file:
            data = file.read()
            file_bytes = struct.pack(">Q", len(data)) + data
        num_padding_bytes = 2048 - len(file_bytes) % 2048
        image = np.frombuffer(file_bytes + b"\0" * num_padding_bytes, dtype=np.uint8).reshape((-1, 2048))
        with open(f"{filename}.txt", "w") as text_file:
            for i in range(0, image.shape[0], 2048):
                image_name = f"{filename}.{i//2048}.png"
                Image.fromarray(image[i:i+2048], "L").save(image_name)
                text_file.write(f"{image_name}\n")
        with open(f"{filename}_links.txt", "w") as links_file:
            with open(f"{filename}.txt", "r") as text_file:
                for line in text_file:
                    image_path = line.strip()
                    upload = anon.upload(image_path, progressbar=True)
                    links_file.write(f"{upload.url.geturl()} {image_path}\n")
    if not error:
        print("The files have been successfully encoded and uploaded!")
def decode_file(original_filename):
    filepath = os.path.join(os.path.dirname(os.path.abspath(original_filename)), original_filename)
    if ".0.png" not in filepath: return
    image_data = []
    i = 0
    while True:
        try:
            image_data.append(np.array(Image.open(f"{filepath[:-6]}.{i}.png")))
        except:
            break
        i += 1
    file_bytes = np.concatenate(image_data).tobytes()
    file_size = int.from_bytes(file_bytes[:8], 'big')
    output_path = os.path.join(os.path.dirname(filepath), original_filename[:-6])
    with open(output_path, "wb") as output_file:
        output_file.write(file_bytes[8:file_size+8])
    print(f"The file has been successfully decoded to: {output_path}")
    for j in range(i):
        os.remove(f"{filepath[:-6]}.{j}.png")
    display_image(output_path)
def update_listbox():
    listbox.delete(0, 'end')
    [listbox.insert('end', file[:-10]) for file in os.listdir() if file.endswith("_links.txt")]
def process_file(filename):
    with open(filename, "r") as links_file:
        url, original_filename = links_file.readline().strip().split()
        links = [url] + [line.strip() for line in links_file]
    target_dir = os.path.dirname(os.path.abspath(filename))
    decoded_file_path = os.path.join(target_dir, original_filename[:-6])
    if os.path.exists(decoded_file_path):
        display_image(decoded_file_path)
    else:
        anon = AnonFile()
        for url in links:
            download_response = anon.download(url, path=target_dir)
            print(f"File downloaded to: {download_response}")
        decode_file(original_filename)
def on_select(event):
    process_file(listbox.get(listbox.curselection()[0]) + '_links.txt')

def load_gallery():
    for i in range(listbox.size()):
        process_file(listbox.get(i) + '_links.txt')
def display_image(image_path):
    for widget in root.winfo_children():
        if isinstance(widget, tk.Label):
            widget.destroy()
    if image_path.endswith('.0.png'):
        image_path = image_path[:-6]
    try:
        image = Image.open(image_path)
    except IOError:
        label = tk.Label(root, text="This file format is not supported.")
        label.place(relx=0.6, rely=0.5, anchor='center')
        return
    max_size = 700
    scale_factor = max_size / max(image.size)
    if scale_factor < 1:
        image = image.resize(tuple(map(int, (scale_factor * i for i in image.size))),Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(image)
    label = tk.Label(root, image=photo)
    label.image = photo
    label.place(relx=0.6, rely=0.5, anchor='center')
root = tk.Tk()
root.title("Hidecen")
root.geometry("1280x720")
root.resizable(0, 0)
tk.Button(root, text="Encode the file", command=lambda: [encode_file(), update_listbox()]).pack(anchor='w')
tk.Button(root, text="Load gallery", command=load_gallery).pack(anchor='w')
listbox=tk.Listbox(root)
listbox.pack(anchor='w')
listbox.config(width=60,height=38)
listbox.bind('<<ListboxSelect>>', on_select)
update_listbox()
root.mainloop()