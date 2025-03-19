import os
import subprocess
import customtkinter as ctk
import time
import threading
import yt_dlp
import tkinter as tk
from tkinter import messagebox, filedialog

# -------------------------- INSTALLATION DE FFMPEG --------------------------

def find_ffmpeg_path():
    """Vérifie si FFmpeg est déjà dans le bon dossier."""
    possible_path = r"C:\Program Files\TubeSaver\build\asset"
    return possible_path if os.path.exists(possible_path) else None

def verify_ffmpeg():
    """Vérifie si FFmpeg est installé."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def add_ffmpeg_to_path():
    """Ajoute FFmpeg au PATH si nécessaire."""
    ffmpeg_path = find_ffmpeg_path()
    
    if not ffmpeg_path:
        return False
    
    existing_path = os.environ.get("PATH", "")
    if ffmpeg_path in existing_path:
        return True  # Déjà ajouté
    
    try:
        subprocess.run(f'setx PATH "%PATH%;{ffmpeg_path}"', shell=True)
        os.environ["PATH"] += f";{ffmpeg_path}"  # Mise à jour immédiate
        return True
    except Exception as e:
        print(f"Erreur d'ajout au PATH : {e}")
        return False

def install_ffmpeg_if_needed():
    """Vérifie et installe FFmpeg avant d’exécuter l’application."""
    if not verify_ffmpeg():
        print("FFmpeg non détecté, installation en cours...")
        if add_ffmpeg_to_path():
            print("FFmpeg ajouté au PATH avec succès.")
        else:
            print("Erreur : Impossible d'ajouter FFmpeg au PATH.")
    else:
        print("FFmpeg est déjà installé.")

# -------------------------- LOGIQUE DE TELECHARGEMENT --------------------------

def progress_hook(d):
    if d['status'] == 'downloading':
        total_size = d.get('total_bytes', 0)
        downloaded_size = d.get('downloaded_bytes', 0)
        if total_size > 0:
            # Calculer le pourcentage et mettre à jour la barre de progression
            progress = downloaded_size / total_size
            if progress_bar.get() < progress:  # Ne mettre à jour que si le progrès a augmenté
                progress_bar.set(progress)

def check_file_exists(file_path):
    return os.path.isfile(file_path)

def select_download_directory():
    # Ouvre une boîte de dialogue pour choisir un répertoire
    directory = filedialog.askdirectory(title="Choisissez un dossier pour télécharger")
    return directory

def download_video():
    video_url = url_entry.get().strip()
    if not video_url:
        status_label.configure(text="Veuillez entrer une URL valide.", text_color="red")
        return

    # Demander à l'utilisateur de choisir un dossier de téléchargement
    download_directory = select_download_directory()
    if not download_directory:  # Si aucun dossier n'est sélectionné
        return

    output_file = os.path.join(download_directory, '%(title)s.%(ext)s')

    if check_file_exists(output_file):
        # Si le fichier existe, afficher un message
        messagebox.showinfo("Fichier Existant", f"Le fichier existe déjà : {output_file}")
        return
    
     # Obtenir la qualité choisie dans la liste déroulante
    selected_quality = quality_option.get()

    # Configurer le format en fonction de la qualité choisie
    if selected_quality == "480p":
        format_str = 'bestvideo[height<=480]+bestaudio/best'
    elif selected_quality == "720p":
        format_str = 'bestvideo[height<=720]+bestaudio/best'
    elif selected_quality == "1080p":
        format_str = 'bestvideo[height<=1080]+bestaudio/best'
    elif selected_quality == "1440p":
        format_str = 'bestvideo[height<=1440]+bestaudio/best'
    elif selected_quality == "4K":
        format_str = 'bestvideo[height<=4320]+bestaudio/best'  # 4K = 4320p
    else:
        format_str = 'bestvideo[height<=720]+bestaudio/best'  # Valeur par défaut (720p)


    # Configurer les options de téléchargement pour 720p avec audio AAC
    ydl_opts = {
        'format': format_str,
        'outtmpl': output_file,
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
        'merge_output_format': 'mp4',
        'postprocessor_args': [
            '-c:a', 'aac',
            '-b:a', '192k'
        ],
        'progress_hooks': [progress_hook],  # Ajouter le hook de progression
    }

    progress_bar.set(0)
    status_label.configure(text="Téléchargement en cours...", text_color="white")
    threading.Thread(target=start_download, args=(ydl_opts, video_url)).start()

def download_audio():
    video_url = url_entry.get().strip()
    if not video_url:
        status_label.configure(text="Veuillez entrer une URL valide.", text_color="red")
        return

    # Demander à l'utilisateur de choisir un dossier de téléchargement
    download_directory = select_download_directory()
    if not download_directory:  # Si aucun dossier n'est sélectionné
        return

    output_file = os.path.join(download_directory, '%(title)s.mp3')

    if check_file_exists(output_file):
        messagebox.showinfo("Fichier Existant", f"Le fichier audio existe déjà : {output_file}")
        return

    # Configurer les options de téléchargement uniquement pour l'audio
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_file,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'progress_hooks': [progress_hook],
    }

    progress_bar.set(0)
    status_label.configure(text="Téléchargement audio en cours...", text_color="blue")
    threading.Thread(target=start_download, args=(ydl_opts, video_url)).start()

def start_download(ydl_opts, video_url):
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        app.after(0, lambda: status_label.configure(text="Téléchargement terminé !", text_color="green"))
    except Exception as e:
        print(f"Erreur: {str(e)}")
        app.after(0, lambda err=e: status_label.configure(text=f"Erreur : {str(err)}", text_color="red"))

# -------------------------- INTERFACE UTILISATEUR --------------------------

def start_app():
    global app, url_entry, status_label, progress_bar

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("TubeSaver")
app.geometry("500x400")

# En-tête
header_label = ctk.CTkLabel(app, text="TubeSaver", font=("Helvetica", 18, "bold"))
header_label.pack(pady=(20, 10))

# Entrée d'URL
url_label = ctk.CTkLabel(app, text="Entrez l'URL de la vidéo YouTube :", font=("Helvetica", 12))
url_label.pack(pady=(10, 5))

url_entry = ctk.CTkEntry(app, width=400, placeholder_text="https://www.youtube.com/watch?v=example", font=("Helvetica", 12))
url_entry.pack(pady=(0, 20))


# Liste déroulante pour choisir la qualité
quality_label = ctk.CTkLabel(app, text="Choisissez la qualité :", font=("Helvetica", 12))
quality_label.pack(pady=(10, 5))

quality_options = ["480p", "720p", "1080p", "1440p", "4K"]
quality_option = ctk.CTkComboBox(app, values=quality_options, font=("Helvetica", 12), width=200)
quality_option.set("720p")  # Valeur par défaut
quality_option.pack(pady=(0, 20))

# Boutons de téléchargement
button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=(10, 20))

download_video_button = ctk.CTkButton(button_frame, text="Télécharger Vidéo", command=download_video, width=150)
download_video_button.pack(side=tk.LEFT, padx=(0, 10))

download_audio_button = ctk.CTkButton(button_frame, text="Télécharger Audio", command=download_audio, width=150)
download_audio_button.pack(side=tk.LEFT)

# Étiquette de statut
status_label = ctk.CTkLabel(app, text="", font=("Helvetica", 12))
status_label.pack(pady=(10, 10))

# Ajouter une barre de progression
progress_bar = ctk.CTkProgressBar(app, width=400)
progress_bar.pack(pady=(10, 20))

# Initialiser la barre de progression à zéro
progress_bar.set(0)

app.mainloop()

# -------------------------- EXECUTION PRINCIPALE --------------------------

if __name__ == "__main__":
    install_ffmpeg_if_needed()  # Vérifie et installe FFmpeg
    start_app()  # Lance l'application principale
