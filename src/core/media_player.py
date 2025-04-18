import vlc
import sys
import os

class MediaPlayer:
    """
    Clase que encapsula la funcionalidad del reproductor de medios VLC.
    Esta clase es independiente de la interfaz gráfica y puede ser utilizada
    con cualquier framework de UI.
    """
    
    def __init__(self):
        """Inicializa el reproductor de medios con las opciones predeterminadas"""
        # Inicializar VLC con opciones específicas
        vlc_args = [
            '--embedded-video',  # Forzar video embebido
            '--no-snapshot-preview',  # Deshabilitar vista previa de capturas
            '--avcodec-hw=none',  # Deshabilitar decodificación por hardware
            '--no-direct3d11-hw-blending',  # Deshabilitar mezcla por hardware en Direct3D11
            '--no-direct3d11',  # Deshabilitar Direct3D11
            '--quiet',  # Reducir mensajes de registro
            '--no-video-title-show',  # No mostrar título de video
            '--no-fullscreen',  # Evitar pantalla completa automática
            '--video-on-top',  # Mantener video encima
        ]
        self.instance = vlc.Instance(vlc_args)
        self.player = self.instance.media_player_new()
        
        # Variables para control de video
        self.current_audio_track = 0
        self.audio_tracks = []
        self.current_aspect_ratio = 'auto'
        self.current_scale = 1.0
    
    def set_window_handle(self, window_id):
        """Configura el handle de la ventana donde se mostrará el video"""
        if sys.platform.startswith('win'):
            self.player.set_hwnd(int(window_id))
        elif sys.platform.startswith('linux'):
            self.player.set_xwindow(window_id)
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(window_id))
    
    def play_media(self, url):
        """Reproduce un medio desde la URL proporcionada"""
        if not url:
            return False
            
        try:
            # Configurar opciones de reproducción específicas para este medio
            media = self.instance.media_new(url)
            media.add_option('avcodec-hw=none')  # Deshabilitar decodificación por hardware
            media.add_option('no-direct3d11-hw-blending')  # Deshabilitar mezcla por hardware
            media.add_option('no-direct3d11')  # Deshabilitar Direct3D11
            media.add_option('no-fullscreen')  # Evitar pantalla completa automática
            media.add_option('embedded-video')  # Forzar video embebido
            
            self.player.set_media(media)
            return self.player.play()
        except Exception as e:
            print(f"Error al reproducir medio: {e}")
            return False
    
    def stop(self):
        """Detiene la reproducción actual"""
        return self.player.stop()
    
    def pause(self):
        """Pausa o reanuda la reproducción"""
        return self.player.pause()
    
    def is_playing(self):
        """Verifica si el reproductor está reproduciendo actualmente"""
        return self.player.is_playing()
    
    def get_media(self):
        """Obtiene el medio actual"""
        return self.player.get_media()
    
    def set_scale_mode(self, scale):
        """Cambia la escala del video"""
        try:
            scale = float(scale)
            self.player.video_set_scale(scale)
            self.current_scale = scale
            print(f"Escala de video cambiada a: {scale}")
            return True
        except Exception as e:
            print(f"Error al cambiar la escala del video: {e}")
            return False
    
    def set_aspect_ratio(self, aspect_ratio):
        """Cambia la relación de aspecto del video"""
        try:
            if not self.player.get_media():
                print("No hay medio cargado para cambiar la relación de aspecto")
                return False
            
            # Establecer la relación de aspecto
            self.player.video_set_aspect_ratio(aspect_ratio)
            self.current_aspect_ratio = aspect_ratio
            print(f"Relación de aspecto cambiada a: {aspect_ratio}")
            return True
        except Exception as e:
            print(f"Error al cambiar la relación de aspecto: {e}")
            return False
    
    def get_audio_tracks(self):
        """Obtiene la lista de pistas de audio disponibles"""
        if not self.is_playing():
            return []
        
        media = self.get_media()
        if not media:
            return []
        
        # Obtener la lista de pistas de audio
        tracks = []
        for i in range(self.player.audio_get_track_count()):
            track_description = self.player.audio_get_track_description()[i]
            if track_description:
                tracks.append(track_description)
        
        self.audio_tracks = tracks
        return tracks
    
    def change_audio_track(self, track_id):
        """Cambia la pista de audio actual"""
        try:
            if not self.player.get_media():
                print("No hay medio cargado para cambiar la pista de audio")
                return False
            result = self.player.audio_set_track(track_id)
            if result:
                print(f"Pista de audio cambiada a ID: {track_id}")
                return True
            else:
                print(f"Error al cambiar la pista de audio a ID: {track_id}")
                return False
        except Exception as e:
            print(f"Excepción al cambiar pista de audio: {e}")
            return False
    
    def get_current_audio_track(self):
        """Obtiene la pista de audio actual"""
        if not self.player.get_media():
            return -1
        return self.player.audio_get_track()
