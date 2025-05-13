import tkinter as tk
from tkinter import messagebox
import yt_dlp
import vlc
import threading
import random
import json

bg_color = "black"
fg_color = "#ff00ff"
player = None
results = []
current_index = -1
playlist_mode = False
selected_playlist_name = "Brani Preferiti"
playlists = {"Brani Preferiti": []}
shuffle = False
loop = False

def search_music(query):
    global results
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'noplaylist': True,
        'extract_flat': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_query = f"ytsearch10:{query}"
            data = ydl.extract_info(search_query, download=False)
            results = data['entries']
            listbox.delete(0, tk.END)
            for i, entry in enumerate(results):
                listbox.insert(tk.END, f"{i+1}. {entry['title']}")
        except Exception as e:
            messagebox.showerror("Errore", f"Ricerca fallita: {e}")

def play_audio(url, title, duration):
    global player, current_title
    current_title = title  # Store the current title

    # Ferma il player precedente
    if player:
        player.stop()

    # Crea il nuovo media player
    player = vlc.MediaPlayer(url)
    if not player or not player.get_media():
        print("Errore: il media non è stato caricato correttamente.")
        return

    player.audio_set_volume(100)
    player.play()

    # Attacca l'evento per quando la canzone finisce
    event_manager = player.event_manager()
    if event_manager:
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached)
    else:
        print("Errore: impossibile ottenere l'event manager.")

    # Aggiorna la UI con lo stato
    status_label.config(text=f"🎶 In riproduzione: {title}", fg=fg_color)

def play_selected(index):
    global current_index, playlist_mode
    playlist_mode = False
    current_index = index  # Aggiorna l'indice attuale
    entry_data = results[index]
    with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
        info = ydl.extract_info(entry_data['url'], download=False)
        play_audio(info['url'], info['title'], info.get("duration", 0))

def play_from_playlist(index):
    global current_index, playlist_mode
    playlist_mode = True
    current_index = index  # Aggiorna l'indice della playlist
    entry_data = playlists[selected_playlist_name][index]
    with yt_dlp.YoutubeDL({'format': 'bestaudio/best', 'quiet': True}) as ydl:
        info = ydl.extract_info(entry_data['url'], download=False)
        play_audio(info['url'], info['title'], info.get("duration", 0))

def threaded_search(event=None):
    query = entry.get()
    if query:
        threading.Thread(target=search_music, args=(query,), daemon=True).start()

def threaded_play(index):
    threading.Thread(target=play_selected, args=(index,), daemon=True).start()

def on_select(event):
    selection = listbox.curselection()
    if selection:
        threaded_play(selection[0])

def add_to_playlist():
    selected_song_index = listbox.curselection()
    if selected_song_index:
        selected_song = results[selected_song_index[0]]
        save_to_playlist(selected_song)

def save_to_playlist(song_path):
    playlist_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    for widget in playlist_frame.winfo_children():
        widget.destroy()

    tk.Label(playlist_frame, text="Aggiungi a Playlist", fg="white", bg="#1e1e1e", font=("Courier", 14)).pack(pady=10)

    # Crea una Listbox con selezione multipla
    playlist_listbox = tk.Listbox(playlist_frame, selectmode=tk.MULTIPLE, bg=bg_color, fg="white", selectbackground=fg_color, font=("Courier", 12))
    playlist_listbox.pack(padx=20, pady=10, fill="both", expand=True)

    # Popola la Listbox con i nomi delle playlist
    for playlist_name in playlists.keys():
        playlist_listbox.insert(tk.END, playlist_name)

    def save():
        selected_indices = playlist_listbox.curselection()
        if selected_indices:
            for index in selected_indices:
                selected_playlist = playlist_listbox.get(index)
                if selected_playlist in playlists:
                    playlists[selected_playlist].append(song_path)
                    # Salva la playlist aggiornata su file
                    with open(f"{selected_playlist}.json", "w") as f:
                        json.dump(playlists[selected_playlist], f)
        playlist_frame.pack_forget()  # Torna alla schermata principale

    tk.Button(playlist_frame, text="Aggiungi", command=save, bg=fg_color, fg=bg_color, font=("Courier", 12)).pack(pady=10)
def create_new_playlist():
    def save_playlist():
        name = entry.get()
        if name:
            playlists[name] = []
            with open(f"{name}.json", "w") as f:
                json.dump([], f)
        playlist_frame.pack_forget()  # Torna alla schermata principale

    playlist_frame.pack(side=tk.RIGHT, fill=tk.Y)

    for widget in playlist_frame.winfo_children():
        widget.destroy()

    tk.Label(playlist_frame, text="Crea nuova Playlist", fg="white", bg="#1e1e1e").pack()
    entry = tk.Entry(playlist_frame)
    entry.pack()
    tk.Button(playlist_frame, text="Salva", command=save_playlist).pack()

def update_playlist_display():
    playlist_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    for widget in playlist_frame.winfo_children():
        widget.destroy()

    playlist_names = list(playlists.keys())
    selected_playlist = tk.StringVar(root)
    selected_playlist.set("Brani Preferiti")

    def update_listbox(*args):
        selected_playlist_name = selected_playlist.get()
        pl_listbox.delete(0, tk.END)
        for i, song in enumerate(playlists[selected_playlist_name]):
            pl_listbox.insert(tk.END, f"{i+1}. {song['title']}")

    selected_playlist.trace("w", update_listbox)
    tk.OptionMenu(playlist_frame, selected_playlist, *playlists.keys()).pack(pady=10)

    pl_listbox = tk.Listbox(playlist_frame, bg=bg_color, fg="white", selectbackground=fg_color, font=("Courier", 12))
    pl_listbox.pack(padx=20, pady=10, fill="both", expand=True)

    def remove_selected_song():
        sel = pl_listbox.curselection()
        if sel:
            selected_index = sel[0]
            selected_playlist_name = selected_playlist.get()
            song = playlists[selected_playlist_name][selected_index]

            # Conferma la rimozione
            confirm = messagebox.askyesno("Conferma Rimozione", f"Vuoi rimuovere '{song['title']}' dalla playlist?")
            if confirm:
                playlists[selected_playlist_name].pop(selected_index)
                update_listbox()  # Aggiorna la lista
                # Salva la playlist aggiornata su file
                with open(f"{selected_playlist_name}.json", "w") as f:
                    json.dump(playlists[selected_playlist_name], f)

    # Aggiungi il pulsante per rimuovere il brano selezionato
    tk.Button(playlist_frame, text="Rimuovi Brano", command=remove_selected_song, bg="red", fg="white", font=("Courier", 10)).pack(pady=10)

    pl_listbox.bind('<Double-1>', lambda _: play_from_playlist(pl_listbox.curselection()[0]))
    update_listbox()

    tk.Button(playlist_frame, text="🆕 Crea Playlist", command=create_new_playlist, bg=fg_color, fg=bg_color, font=("Courier", 12)).pack(pady=10)

def pause_music():
    global current_title
    if player:
        if player.is_playing():
            # Metti in pausa la riproduzione
            player.pause()
            status_label.config(text="⏸ In pausa", fg="white")
        else:
            # Riprendi la riproduzione
            player.play()
            status_label.config(text=f"🎶 In riproduzione: {current_title}", fg=fg_color)

def stop_music():
    global timer_running
    if player:
        player.stop()
        timer_running = False
    status_label.config(text="⛔ Riproduzione fermata")
    timer_label.config(text="")

def skip_next():
    global current_index
    if shuffle:
        if playlist_mode:
            if playlists[selected_playlist_name]:
                current_index = random.randint(0, len(playlists[selected_playlist_name]) - 1)
                play_from_playlist(current_index)
        else:
            if results:
                current_index = random.randint(0, len(results) - 1)
                play_selected(current_index)
    else:
        if playlist_mode:
            if current_index + 1 < len(playlists[selected_playlist_name]):
                play_from_playlist(current_index + 1)
            elif loop:
                play_from_playlist(0)
        else:
            if current_index + 1 < len(results):
                play_selected(current_index + 1)
            elif loop:
                play_selected(0)

def skip_previous():
    global current_index
    if current_index > 0:
        if playlist_mode:
            play_from_playlist(current_index - 1)
        else:
            play_selected(current_index - 1)

def on_end_reached(event):
    print("Traccia terminata, avanzamento alla successiva...")
    global current_index, playlist_mode
    if playlist_mode:
        if current_index + 1 < len(playlists[selected_playlist_name]):
            play_from_playlist(current_index + 1)
        elif loop:  # Ripeti la playlist se il loop è attivo
            play_from_playlist(0)
    else:
        if current_index + 1 < len(results):
            play_selected(current_index + 1)
        elif loop:  # Ripeti la ricerca se il loop è attivo
            play_selected(0)

root = tk.Tk()
root.title("MYTAH")
root.configure(bg=bg_color)
root.geometry("900x600")

shuffle_loop_frame = tk.Frame(root, bg=bg_color)
shuffle_loop_frame.pack(pady=10)

def toggle_shuffle():
    global shuffle
    shuffle = not shuffle
    shuffle_button.config(text=f"Shuffle {'ON' if shuffle else 'OFF'}", fg="white" if shuffle else "red")

def toggle_loop():
    global loop
    loop = not loop
    loop_button.config(text=f"Loop {'ON' if loop else 'OFF'}", fg="white" if loop else "red")

shuffle_button = tk.Button(shuffle_loop_frame, text="Shuffle OFF", command=toggle_shuffle, bg=bg_color, fg="red", font=("Courier", 12))
shuffle_button.pack(side="left", padx=5)

loop_button = tk.Button(shuffle_loop_frame, text="Loop OFF", command=toggle_loop, bg=bg_color, fg="red", font=("Courier", 12))
loop_button.pack(side="left", padx=5)

tk.Label(root, text="Cerca su MYTAH:", bg=bg_color, fg=fg_color, font=("Courier", 14)).pack(pady=10)

entry = tk.Entry(root, width=40, font=("Courier", 12), bg=bg_color, fg=fg_color, insertbackground=fg_color)
entry.pack()
entry.bind("<Return>", threaded_search)

btn_frame = tk.Frame(root, bg=bg_color)
btn_frame.pack(pady=5)
tk.Button(btn_frame, text="🔍 Cerca", command=threaded_search, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)
tk.Button(btn_frame, text="⏮", command=skip_previous, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)
tk.Button(btn_frame, text="⏸ Pausa", command=pause_music, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)
tk.Button(btn_frame, text="⏹ Stop", command=stop_music, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)
tk.Button(btn_frame, text="⏭", command=skip_next, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)

playlist_btn_frame = tk.Frame(root, bg=bg_color)
playlist_btn_frame.pack(pady=10)
tk.Button(playlist_btn_frame, text="Aggiungi a Playlist", command=add_to_playlist, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)
tk.Button(playlist_btn_frame, text="Mostra Playlist", command=update_playlist_display, font=("Courier", 12), bg=fg_color, fg=bg_color).pack(side="left", padx=5)

listbox = tk.Listbox(root, bg=bg_color, fg="white", selectbackground=fg_color, font=("Courier", 10))
listbox.pack(padx=10, pady=10, fill="both", expand=True)
listbox.bind('<Double-1>', on_select)

status_frame = tk.Frame(root, bg=bg_color)
status_frame.pack()

status_label = tk.Label(status_frame, text="", bg=bg_color, fg=fg_color, font=("Courier", 10))
status_label.pack(side="left", padx=10)

timer_label = tk.Label(status_frame, text="", bg=bg_color, fg=fg_color, font=("Courier", 10))
timer_label.pack(side="left", padx=10)

playlist_frame = tk.Frame(root, bg=bg_color)

root.mainloop()