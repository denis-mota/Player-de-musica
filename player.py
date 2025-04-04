# Music and Audio Player for Windows

# Import required libraries
import flet as ft
from playsound import playsound
import os
from pathlib import Path
import random
import threading
import time

def main(page: ft.Page):
    page.title = "Music Player"
    page.bgcolor = ft.Colors.GREY_900  # Atualizado para Colors
    page.padding = 0
    page.window_width = 200 # 495
    page.window_height = 520
    page.window_title_bar_hidden = True
    page.window_bgcolor = ft.Colors.TRANSPARENT  # Atualizado para Colors
    page.window_border_radius = 10
    
    # Variáveis de estado do player
    current_track = None
    is_playing = False
    is_muted = False
    is_loop = False
    is_random = False
    playlist = []
    current_index = 0
    current_position = 0
    track_duration = 0  # Estimativa
    last_volume = 100
    
    # Estado do player
    play_thread = None
    start_time = 0
    is_stopped = False
    track_ended = False
    timer = None
    
    # File picker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)
    supported_formats = ["mp3", "wav"]
    
    # UI Controls
    header = ft.Text(
        value="Selecione uma música",
        size=10,
        color=ft.Colors.WHITE,  # Atualizado para Colors
        weight=ft.FontWeight.BOLD   
    )
    
    # Progress bar and time counter
    progress = ft.ProgressBar(
        width=300,
        value=0
    )
    
    # Time counter
    time_counter = ft.Text(
        value="0:00 / 0:00",
        size=14,
        color=ft.Colors.WHITE  # Atualizado para Colors
    )
    
    # Control buttons
    button_style = {
        "width": 40,
        "height": 40,
        "bgcolor": ft.Colors.GREY_800,  # Atualizado para Colors
        "icon_color": ft.Colors.WHITE,  # Atualizado para Colors
    }
    
    play_btn = ft.IconButton(
        icon=ft.Icons.PLAY_ARROW,  # Atualizado para Icons
        **button_style
    )
    
    prev_btn = ft.IconButton(
        icon=ft.Icons.SKIP_PREVIOUS,  # Atualizado para Icons
        **button_style
    )
    
    next_btn = ft.IconButton(
        icon=ft.Icons.SKIP_NEXT,  # Atualizado para Icons
        **button_style
    )
    
    stop_btn = ft.IconButton(
        icon=ft.Icons.STOP,  # Atualizado para Icons
        **button_style
    )
    
    loop_btn = ft.IconButton(
        icon=ft.Icons.REPEAT,  # Atualizado para Icons
        **button_style
    )
    
    random_btn = ft.IconButton(
        icon=ft.Icons.SHUFFLE,  # Atualizado para Icons
        **button_style
    )
    
    # Volume control
    volume_slider = ft.Slider(
        min=0,
        max=100,
        value=100,
        width=100
    )
    
    mute_btn = ft.IconButton(
        icon=ft.Icons.VOLUME_UP,  # Atualizado para Icons
        **button_style
    )
    
    # Album art placeholder
    img_path = Path("img/music.jpg")
    art_container = ft.Container(
        width=300,
        height=225,
        bgcolor=ft.Colors.GREY_800  # Atualizado para Colors
    )
    
    if img_path.exists():
        art_container.content = ft.Image(
            src=str(img_path),
            width=300,
            height=300,
            fit=ft.ImageFit.CONTAIN,
            border_radius=10
        )
        art_container.border_radius = 10
    
    # Funções do player
    def format_time(seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def update_progress():
        """Update progress bar and time counter"""
        nonlocal current_position
        
        if is_playing and not is_stopped:
            # Calcular a posição atual com base no tempo
            current_position = min(time.time() - start_time, track_duration)
            
            # Update progress bar
            if track_duration > 0:
                progress_value = min(current_position / track_duration, 1.0)
                progress.value = progress_value
                
                # Update time counter
                time_text = f"{format_time(current_position)} / {format_time(track_duration)}"
                time_counter.value = time_text
                
                # Update UI
                page.update()
                
                # Schedule next update
                return True
        return False
    
    def start_progress_timer():
        """Start timer to update progress"""
        nonlocal timer
        
        if timer:
            stop_progress_timer()
        
        def timer_func():
            nonlocal timer
            if update_progress():
                # Se update_progress retornar True, agendar próxima execução
                timer = threading.Timer(0.1, timer_func)
                timer.daemon = True
                timer.start()
        
        # Iniciar o timer
        timer = threading.Timer(0.1, timer_func)
        timer.daemon = True
        timer.start()
    
    def stop_progress_timer():
        """Stop progress timer"""
        nonlocal timer
        if timer:
            timer.cancel()
            timer = None
    
    def play_sound_thread(track_path):
        """Função para reproduzir o som em uma thread separada"""
        nonlocal is_stopped, track_ended, is_playing
        
        try:
            playsound(track_path, block=True)
            # Se chegou aqui e não foi parado, a música terminou naturalmente
            if not is_stopped and is_playing:
                track_ended = True
                # Handle track end
                page.invoke_async(handle_track_end)
        except Exception as e:
            print(f"Erro ao reproduzir: {e}")
    
    def handle_track_end():
        """Handle track end event"""
        if is_loop:
            play_current_track()
        else:
            next_track(None)
    
    def on_file_picker_result(e):
        nonlocal playlist, current_index, current_track
        
        if e.files:
            # Clear current playlist
            playlist = []
            
            # Add only MP3 and WAV files to playlist
            for f in e.files:
                file_ext = Path(f.path).suffix.lower()[1:]
                if file_ext in supported_formats:
                    playlist.append(f.path)
            
            # Update UI if files were added
            if playlist:
                current_index = 0
                current_track = playlist[current_index]
                header.value = os.path.basename(current_track)
                page.update()
    
    def load_track(e=None):
        nonlocal current_track
        
        # If no files have been selected, show file picker
        if not playlist:
            file_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=supported_formats
            )
        elif playlist:
            current_track = playlist[current_index]
    
    def play_pause(e):
        nonlocal is_playing, is_stopped, play_thread, start_time
        
        if not current_track:
            load_track()
            if not current_track:
                return
            play_current_track()
            return
        
        if is_playing:
            # Pause playback - com playsound temos que parar completamente
            is_playing = False
            is_stopped = True
            play_btn.icon = ft.Icons.PLAY_ARROW  # Atualizado para Icons
            stop_progress_timer()
        else:
            # Resume playback - com playsound temos que reiniciar
            play_current_track()
        
        page.update()
    
    def stop(e):
        nonlocal is_playing, is_stopped
        
        # Stop playback
        is_playing = False
        is_stopped = True
        play_btn.icon = ft.Icons.PLAY_ARROW  # Atualizado para Icons
        stop_progress_timer()
        
        # Reset progress bar and time counter
        progress.value = 0
        time_counter.value = "0:00 / 0:00"
        page.update()
    
    def prev_track(e):
        nonlocal current_index, current_track
        
        if not playlist:
            return
            
        if is_random:
            current_index = random.randint(0, len(playlist) - 1)
        else:
            current_index = (current_index - 1) % len(playlist)
        current_track = playlist[current_index]
        play_current_track()
    
    def next_track(e):
        nonlocal current_index, current_track
        
        if not playlist:
            return
            
        if is_random:
            current_index = random.randint(0, len(playlist) - 1)
        else:
            current_index = (current_index + 1) % len(playlist)
        current_track = playlist[current_index]
        play_current_track()
    
    def play_current_track():
        nonlocal is_stopped, is_playing, track_ended, start_time, play_thread, track_duration
        
        # Parar qualquer reprodução atual
        is_stopped = True
        if play_thread and play_thread.is_alive():
            # Aguardar a thread atual terminar
            time.sleep(0.1)
        
        # Resetar estado
        is_stopped = False 
        is_playing = True
        track_ended = False
        
        # Atualizar UI
        play_btn.icon = ft.Icons.PAUSE  # Atualizado para Icons
        header.value = os.path.basename(current_track)
        
        # Estimar a duração - playsound não fornece informações de duração
        # Vamos usar uma estimativa padrão de 3 minutos
        track_duration = 180  # 3 minutos em segundos
        
        # Iniciar reprodução em uma thread separada
        start_time = time.time()
        play_thread = threading.Thread(target=play_sound_thread, args=(current_track,))
        play_thread.daemon = True
        play_thread.start()
        
        # Iniciar timer para atualizar a barra de progresso
        start_progress_timer()
        page.update()
    
    def toggle_loop(e):
        nonlocal is_loop
        is_loop = not is_loop
        loop_btn.bgcolor = ft.Colors.GREY_600 if is_loop else ft.Colors.GREY_800  # Atualizado para Colors
        page.update()
    
    def toggle_random(e):
        nonlocal is_random
        is_random = not is_random
        random_btn.bgcolor = ft.Colors.GREY_600 if is_random else ft.Colors.GREY_800  # Atualizado para Colors
        page.update()
    
    def set_volume(e):
        # Playsound não suporta controle de volume
        # Esta função agora é apenas visual
        pass
    
    def toggle_mute(e):
        nonlocal is_muted, last_volume
        # Playsound não suporta controle de volume
        # Esta função agora é apenas visual
        is_muted = not is_muted
        if is_muted:
            last_volume = volume_slider.value
            volume_slider.value = 0
        else:
            volume_slider.value = last_volume
        
        mute_btn.icon = ft.Icons.VOLUME_OFF if is_muted else ft.Icons.VOLUME_UP  # Atualizado para Icons
        page.update()
    
    # Configurar handlers para eventos
    file_picker.on_result = on_file_picker_result
    play_btn.on_click = play_pause
    prev_btn.on_click = prev_track
    next_btn.on_click = next_track
    stop_btn.on_click = stop
    loop_btn.on_click = toggle_loop
    random_btn.on_click = toggle_random
    volume_slider.on_change = set_volume
    mute_btn.on_click = toggle_mute
    
    # Custom title bar sem botão de fechar
    title_text = ft.Text(
        value="Music Player",
        size=16,
        color=ft.Colors.WHITE,  # Atualizado para Colors
        weight=ft.FontWeight.BOLD
    )
    
    # Title bar container
    title_bar = ft.Container(
        content=ft.Row(
            controls=[
                title_text,
                ft.Container(expand=True),  # Spacer
                # Botão de fechar removido
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.only(left=10, right=5, top=5, bottom=5),
        bgcolor=ft.Colors.GREY_900,  # Atualizado para Colors
        border_radius=ft.border_radius.only(top_left=10, top_right=10)
    )
    
    # Add file picker button
    pick_files_btn = ft.ElevatedButton(
        "Selecionar músicas",
        icon=ft.Icons.UPLOAD_FILE,  # Atualizado para Icons
        on_click=lambda _: file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=supported_formats
        )
    )
    
    # Controls row
    controls = ft.Row(
        controls=[
            prev_btn,
            play_btn,
            next_btn,
            stop_btn,
            loop_btn,
            random_btn,
            volume_slider,
            mute_btn
        ],
        alignment=ft.MainAxisAlignment.CENTER
    )
    
    # Progress bar with time counter row
    progress_row = ft.Row(
        controls=[
            progress,
            time_counter
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )
    
    # Main layout
    main_content = ft.Column(
        controls=[
            title_bar,
            header,
            pick_files_btn,
            art_container,
            progress_row,
            controls
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20
    )
    
    # Criar um container principal com bordas arredondadas
    main_container = ft.Container(
        content=main_content,
        bgcolor=ft.Colors.GREY_900,  # Atualizado para Colors
        border_radius=10,
        width=495,
        height=650,
    )
    
    page.add(main_container)

if __name__ == "__main__":
    ft.app(target=main)
