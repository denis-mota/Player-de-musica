# Music and Audio Player for Windows

# Import required libraries
import flet as ft
import pygame
import os
from pathlib import Path
import random
import threading
import time

class MusicPlayer(ft.UserControl):
    def __init__(self):
        super().__init__()
        # Initialize pygame mixer only (without video)
        pygame.init()
        pygame.mixer.init()
        
        # Track state
        self.current_track = None
        self.is_playing = False
        self.is_muted = False
        self.is_loop = False
        self.is_random = False
        self.playlist = []
        self.current_index = 0
        self.current_position = 0
        self.track_duration = 0
        self.last_volume = 100
        # Window dimensions
        self.width = 495  # Window width
        self.height = 520  # Window height
        
        # File picker for MP3 and WAV files
        self.file_picker = ft.FilePicker(on_result=self.on_file_picker_result)
        self.supported_formats = ["mp3", "wav"]
        
        # Set up end of track event
        pygame.mixer.music.set_endevent(pygame.USEREVENT)
        
        # Timer for updating progress bar
        self.timer = None
        
        # Flag to track if a song just ended
        self.track_ended = False
        
        # Start a thread to check for pygame events
        self.event_thread = threading.Thread(target=self.check_events)
        self.event_thread.daemon = True
        self.event_thread.start()
    
    def did_mount(self):
        # Armazena a referência à página quando o controle é montado
        self.page_ref = self.page
        
    def build(self):
        # Custom title bar with close button
        self.title_text = ft.Text(
            value="Music Player",
            size=16,
            color=ft.colors.WHITE,
            weight=ft.FontWeight.BOLD
        )
        
        self.close_btn = ft.IconButton(
            icon=ft.icons.CLOSE,
            icon_color=ft.colors.WHITE,
            on_click=self.close_app,
            tooltip="Fechar"
        )
        
        # Title bar container
        title_bar = ft.Container(
            content=ft.Row(
                controls=[
                    self.title_text,
                    ft.Container(expand=True),  # Spacer
                    self.close_btn
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            padding=ft.padding.only(left=10, right=5, top=5, bottom=5),  # Adjust the top margin to 0
            bgcolor=ft.colors.GREY_900,
            border_radius=ft.border_radius.only(top_left=10, top_right=10)
        )
        
        # Header - Song title
        self.header = ft.Text(
            value="Seleciona uma música",
            size=10,
            color=ft.colors.WHITE,
            weight=ft.FontWeight.BOLD   
        )
        
        # Add file picker button
        self.pick_files_btn = ft.ElevatedButton(
            "Selecionar músicas",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: self.file_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=["mp3", "wav"]
            )
        )
        
        # Album art placeholder
        img_path = Path("img/music.jpg")
        self.art_container = ft.Container(
            width=300,
            height=225,
            bgcolor=ft.colors.GREY_800
        )
        
        if img_path.exists():
            self.art_container.content = ft.Image(
                src=str(img_path),
                width=300,
                height=300,
                fit=ft.ImageFit.CONTAIN,
                border_radius=10  # Adding rounded corners to the image
            )
            self.art_container.border_radius = 10  # Adding rounded corners to the container
            
        # Progress bar and time counter
        self.progress = ft.ProgressBar(
            width=300,
            value=0
        )
        
        # Time counter
        self.time_counter = ft.Text(
            value="0:00 / 0:00",
            size=14,
            color=ft.colors.WHITE
        )
        
        # Control buttons
        button_style = {
            "width": 40,
            "height": 40,
            "bgcolor": ft.colors.GREY_800,
            "icon_color": ft.colors.WHITE,
        }
        
        self.prev_btn = ft.IconButton(
            icon=ft.icons.SKIP_PREVIOUS,
            on_click=self.prev_track,
            **button_style
        )
        
        self.play_btn = ft.IconButton(
            icon=ft.icons.PLAY_ARROW,
            on_click=self.play_pause,
            **button_style
        )
        
        self.next_btn = ft.IconButton(
            icon=ft.icons.SKIP_NEXT,
            on_click=self.next_track,
            **button_style
        )
        
        self.stop_btn = ft.IconButton(
            icon=ft.icons.STOP,
            on_click=self.stop,
            **button_style
        )
        
        self.loop_btn = ft.IconButton(
            icon=ft.icons.REPEAT,
            on_click=self.toggle_loop,
            **button_style
        )
        
        self.random_btn = ft.IconButton(
            icon=ft.icons.SHUFFLE,
            on_click=self.toggle_random,
            **button_style
        )
        
        # Volume control
        self.volume_slider = ft.Slider(
            min=0,
            max=100,
            value=100,
            on_change=self.set_volume,
            width=100
        )
        
        self.mute_btn = ft.IconButton(
            icon=ft.icons.VOLUME_UP,
            on_click=self.toggle_mute,
            **button_style
        )
        
        # Controls row
        controls = ft.Row(
            controls=[
                self.prev_btn,
                self.play_btn,
                self.next_btn,
                self.stop_btn,
                self.loop_btn,
                self.random_btn,
                self.volume_slider,
                self.mute_btn
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Progress bar with time counter row
        progress_row = ft.Row(
            controls=[
                self.progress,
                self.time_counter
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
        
        return ft.Column(
            controls=[
                title_bar,  # Adicionando a barra de título personalizada
                self.header,
                self.pick_files_btn,
                self.art_container,
                progress_row,
                controls
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
            
    def on_file_picker_result(self, e: ft.FilePickerResultEvent):
        if e.files:
            # Clear current playlist
            self.playlist = []
            
            # Add only MP3 and WAV files to playlist
            for f in e.files:
                file_ext = Path(f.path).suffix.lower()[1:]
                if file_ext in self.supported_formats:
                    self.playlist.append(f.path)
            
            # Update UI if files were added
            if self.playlist:
                self.current_index = 0
                self.current_track = self.playlist[self.current_index]
                self.header.value = os.path.basename(self.current_track)
                self.header.update()
    
    def load_track(self, e=None):
        # If no files have been selected, show file picker
        if not self.playlist:
            self.file_picker.pick_files(
                allow_multiple=True,
                allowed_extensions=self.supported_formats
            )
        elif self.playlist:
            self.current_track = self.playlist[self.current_index]
            
    def play_pause(self, e):
        if not self.current_track:
            self.load_track()
            if not self.current_track:
                return
            self.play_current_track()
            return
        
        if self.is_playing:
            pygame.mixer.music.pause()
            self.play_btn.icon = ft.icons.PLAY_ARROW
            self.stop_progress_timer()
        else:
            pygame.mixer.music.unpause()
            self.play_btn.icon = ft.icons.PAUSE
            self.start_progress_timer()
        self.is_playing = not self.is_playing
        self.play_btn.update()
        
    def stop(self, e):
        pygame.mixer.music.stop()
        self.is_playing = False
        self.play_btn.icon = ft.icons.PLAY_ARROW
        self.play_btn.update()
        self.stop_progress_timer()
        
        # Reset progress bar and time counter
        self.progress.value = 0
        self.time_counter.value = "0:00 / 0:00"
        self.progress.update()
        self.time_counter.update()
        
    def prev_track(self, e):
        if not self.playlist:
            return
            
        if self.is_random:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index - 1) % len(self.playlist)
        self.current_track = self.playlist[self.current_index]
        self.play_current_track()
        
    def next_track(self, e):
        if not self.playlist:
            return
            
        if self.is_random:
            self.current_index = random.randint(0, len(self.playlist) - 1)
        else:
            self.current_index = (self.current_index + 1) % len(self.playlist)
        self.current_track = self.playlist[self.current_index]
        self.play_current_track()
        
    def play_current_track(self):
        pygame.mixer.music.load(self.current_track)
        pygame.mixer.music.play()
        self.is_playing = True
        self.track_ended = False  # Reset track ended flag
        self.play_btn.icon = ft.icons.PAUSE
        self.play_btn.update()
        self.header.value = os.path.basename(self.current_track)
        self.header.update()
        
        # Get track duration
        sound = pygame.mixer.Sound(self.current_track)
        self.track_duration = sound.get_length()
        
        # Start progress timer
        self.start_progress_timer()
        
    def toggle_loop(self, e):
        self.is_loop = not self.is_loop
        self.loop_btn.bgcolor = ft.colors.GREY_600 if self.is_loop else ft.colors.GREY_800
        self.loop_btn.update()
        
    def toggle_random(self, e):
        self.is_random = not self.is_random
        self.random_btn.bgcolor = ft.colors.GREY_600 if self.is_random else ft.colors.GREY_800
        self.random_btn.update()
        
    def set_volume(self, e):
        volume = float(e.control.value) / 100
        pygame.mixer.music.set_volume(volume)
        
    def toggle_mute(self, e):
        self.is_muted = not self.is_muted
        if self.is_muted:
            self.last_volume = self.volume_slider.value
            pygame.mixer.music.set_volume(0)
            self.volume_slider.value = 0
        else:
            pygame.mixer.music.set_volume(self.last_volume / 100)
            self.volume_slider.value = self.last_volume
        self.mute_btn.icon = ft.icons.VOLUME_OFF if self.is_muted else ft.icons.VOLUME_UP
        self.mute_btn.update()
        self.volume_slider.update()
        
    def format_time(self, seconds):
        """Format seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
    
    def check_events(self):
        """Thread function to check for pygame events"""
        while True:
            # Verificar se a música terminou usando get_busy()
            if self.is_playing and not pygame.mixer.music.get_busy() and not self.track_ended:
                # A música terminou, mas o flag ainda não foi acionado
                self.track_ended = True
                # Usar threading para chamar o método de tratamento em thread segura
                threading.Thread(target=self.handle_track_end).start()
            # Sleep to avoid high CPU usage
            time.sleep(0.1)
            
    def handle_track_end(self):
        """Handle track end event in a thread-safe way"""
        if self.is_loop:
            self.play_current_track()
        else:
            self.next_track(None)
    
    def update_progress(self):
        """Update progress bar and time counter"""
        if self.is_playing and pygame.mixer.music.get_busy():
            self.current_position = pygame.mixer.music.get_pos() / 1000  # Convert ms to seconds
            
            # Update progress bar
            if self.track_duration > 0:
                progress_value = self.current_position / self.track_duration
                self.progress.value = progress_value
                
                # Update time counter
                time_text = f"{self.format_time(self.current_position)} / {self.format_time(self.track_duration)}"
                self.time_counter.value = time_text
                
                # Update UI
                self.progress.update()
                self.time_counter.update()
                
                # Schedule next update
                return True
        return False
    
    def start_progress_timer(self):
        """Start timer to update progress"""
        import threading
        
        if self.timer:
            self.stop_progress_timer()
        
        # Define a função que executa update_progress periodicamente
        def timer_func():
            if self.update_progress():
                # Se update_progress retornar True, agendar próxima execução
                self.timer = threading.Timer(0.1, timer_func)  # Update every 100ms
                self.timer.daemon = True  # Permitir que o programa termine mesmo se o timer estiver rodando
                self.timer.start()
        
        # Iniciar o timer
        self.timer = threading.Timer(0.1, timer_func)
        self.timer.daemon = True
        self.timer.start()
    
    def stop_progress_timer(self):
        """Stop progress timer"""
        if self.timer:
            self.timer.cancel()
            self.timer = None
            
    def close_app(self, e):
        """Close the application"""
        if hasattr(self, 'page_ref'):
            self.page_ref.window_close()

def main(page: ft.Page):
    page.title = "Music Player"
    page.bgcolor = ft.colors.GREY_900
    page.padding = 0  # Removendo o padding para a barra de título personalizada ficar alinhada
    page.window_width = 495  # Set window width
    page.window_height = 520  # Set window height
    page.window_title_bar_hidden = True  # Hide window title bar
    page.window_bgcolor = ft.colors.TRANSPARENT  # Fundo transparente
    page.window_border_radius = 10  # Bordas arredondadas para a janela
    
    # Criar um container principal com bordas arredondadas
    main_container = ft.Container(
        content=MusicPlayer(),
        bgcolor=ft.colors.GREY_900,
        border_radius=10,  # Bordas arredondadas
        width=495,
        height=650,
    )
    
    player = main_container.content
    # Add file picker to page overlay
    page.overlay.append(player.file_picker)
    page.add(main_container)

if __name__ == "__main__":
    ft.app(target=main)
