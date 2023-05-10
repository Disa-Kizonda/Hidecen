import tkinter as tk
from tkinter import filedialog, Tk, Listbox, Label, Button
import numpy as np
from PIL import ImageTk,Image
from anonfile import AnonFile
from pathlib import Path
import re,struct,os,random,uuid
from urllib.parse import unquote
api_list = [
	"https://api.letsupload.cc/",
	"https://api.filechan.org/",
	"https://api.anonfiles.com/",
	"https://api.megaupload.nz/",
	"https://api.zippysha.re/",
	"https://api.vshare.is/",
	"https://api.rapidshare.nu/",
	"https://api.myfile.is/",
	"https://api.hotfile.io/",
	"https://api.upvid.cc/",
	"https://api.lolabits.se/"
	]
def encode_file():
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
        num_padding_bytes = int(image_size.get()) - len(file_bytes) % int(image_size.get())
        image = np.frombuffer(file_bytes + b"\0" * num_padding_bytes, dtype=np.uint8).reshape((-1, int(image_size.get())))
        with open(f"{filename}.txt", "w") as text_file:
            for i in range(0, image.shape[0], int(image_size.get())):
                image_name = f"{str(uuid.uuid4())}.png"
                Image.fromarray(image[i:i+int(image_size.get())], "L").save(image_name)
                text_file.write(f"{image_name}\n")
        with open(f"{filename}_links.txt", "w") as links_file:
            with open(f"{filename}.txt", "r") as text_file:
                index = 0
                for line in text_file:
                    AnonFile.API = random.choice(api_list)
                    anon = AnonFile()
                    image_path = line.strip()
                    while True:
                        try:
                            upload = anon.upload(image_path, progressbar=True)
                            break
                        except Exception as e:
                            print(f"Error uploading file: {e}. Retrying...")
                    links_file.write(f"{upload.url.geturl()} {filename}.{index}.png\n")
                    os.remove(image_path)
                    index += 1
        os.remove(f"{filename}.txt")
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
def get_last_created_file(folder_path):
    files = [os.path.join(folder_path, file) for file in os.listdir(folder_path)]
    last_created_file = max(files, key=os.path.getctime)
    return last_created_file
def process_file(filename):
    with open(filename, "r") as links_file:
        url, original_filename = links_file.readline().strip().split(' ', 1)
        links = [url] + [line.strip() for line in links_file]
    target_dir = os.path.dirname(os.path.abspath(filename))
    decoded_file_path = os.path.join(target_dir, unquote(original_filename)[:-6])
    if os.path.exists(decoded_file_path):
        display_image(decoded_file_path)
    else:
        anon = AnonFile()
        for i, url in enumerate(links):
            while True:
                try:
                    download_response = anon.download(url, path=target_dir)
                    break
                except Exception as e:
                    print(f"Error downloading file: {e}. Retrying...")
            old_filename = get_last_created_file(target_dir)
            new_filename = f"{decoded_file_path}.{i}.png"
            os.rename(old_filename, new_filename)
            print(f"File downloaded to: {new_filename}")
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
def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("300x200")
    tk.Label(settings_window, text="Image size:").pack(anchor='w')
    sizes = ["2048", "1024", "512", "256", "128"]
    for size in sizes:
        size_in_bytes = int(size) * int(size)
        size_in_kilobytes = size_in_bytes / 1024
        tk.Radiobutton(settings_window, text=f"{size} ({size_in_kilobytes:.2f} KB)", variable=image_size, value=size).pack(anchor='w')
    def apply_settings():
        settings_window.destroy()
    tk.Button(settings_window, text="Apply", command=apply_settings).pack()
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
image_size = tk.StringVar(value="2048")
tk.Button(root, text="Settings", command=open_settings).place(relx=1.0, rely=0.0, anchor='ne')
root.mainloop()