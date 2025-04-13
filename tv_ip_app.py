import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QComboBox, QFileDialog, QListWidgetItem, QSizePolicy,
                             QProgressDialog, QInputDialog, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction
import vlc
import asyncio
from playlist_manager import PlaylistManager, Channel

class TVIPPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)  # Establecer tamaño mínimo para la ventana
        self.installEventFilter(self)
        
        # Variables para control de panel lateral
        self.sidebar_visible = True
        self.is_fullscreen_mode = False
        self.sidebar_hover_margin = 20  # píxeles desde el borde izquierdo para activar
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)  # verificar cada 100ms
        
        # Inicializar el gestor de listas
        self.playlist_manager = PlaylistManager()
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Panel lateral para lista de canales
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setMinimumWidth(280)  # Ancho mínimo para el panel lateral
        self.sidebar.setMaximumWidth(350)  # Ancho máximo para el panel lateral
        
        # Filtro por grupos
        self.group_filter = QComboBox()
        self.group_filter.addItem('Todos los grupos')
        sidebar_layout.addWidget(QLabel('Filtrar por grupo:'))
        sidebar_layout.addWidget(self.group_filter)
        
        # Lista de canales
        self.channel_list = QListWidget()
        sidebar_layout.addWidget(QLabel('Canales:'))
        sidebar_layout.addWidget(self.channel_list)
        
        # Botones de control - Organizados en grid para mejor visualización
        buttons_layout = QVBoxLayout()
        
        # Primera fila de botones
        top_row_layout = QHBoxLayout()
        load_button = QPushButton('Cargar Lista M3U')
        load_button.clicked.connect(self.load_playlist)
        load_button.setMinimumWidth(140)
        download_button = QPushButton('Descargar Lista')
        download_button.clicked.connect(self.download_playlist)
        download_button.setMinimumWidth(140)
        
        top_row_layout.addWidget(load_button)
        top_row_layout.addWidget(download_button)
        
        # Segunda fila de botones
        bottom_row_layout = QHBoxLayout()
        check_button = QPushButton('Verificar Canales')
        check_button.clicked.connect(self.check_channels)
        check_button.setMinimumWidth(140)
        save_working_button = QPushButton('Guardar Canales Funcionales')
        save_working_button.clicked.connect(self.save_working_channels)
        save_working_button.setMinimumWidth(140)
        
        bottom_row_layout.addWidget(check_button)
        bottom_row_layout.addWidget(save_working_button)
        
        # Agregar las filas al layout principal de botones
        buttons_layout.addLayout(top_row_layout)
        buttons_layout.addLayout(bottom_row_layout)
        
        buttons_container = QWidget()
        buttons_container.setLayout(buttons_layout)
        sidebar_layout.addWidget(buttons_container)
        
        # Área de reproducción
        video_container = QWidget()
        video_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        video_layout = QVBoxLayout(video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        # Instancia de VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Widget para el video
        self.video_widget = QWidget()
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setStyleSheet('background-color: black;')
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        video_layout.addWidget(self.video_widget)
        
        # Controles de video
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        self.fullscreen_button = QPushButton('Pantalla Completa')
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        controls_layout.addWidget(self.fullscreen_button)
        video_layout.addWidget(controls)
        
        # Agregar widgets al layout principal
        layout.addWidget(self.sidebar)
        layout.addWidget(video_container)
        
        # Conectar señales
        self.channel_list.itemClicked.connect(self.play_channel)
        
    def load_playlist(self):
        file_name, _ = QFileDialog.getOpenFileName(self, 'Abrir Lista M3U',
                                                 '', 'M3U Files (*.m3u *.m3u8)')
        if file_name:
            try:
                # Crear diálogo de progreso
                progress = QProgressDialog('Cargando lista de canales...', 'Cancelar', 0, 100, self)
                progress.setWindowModality(Qt.WindowModality.WindowModal)
                progress.setMinimumDuration(0)
                progress.setAutoClose(True)
                progress.setAutoReset(True)
                
                def update_progress(percent, channels_count):
                    if progress.wasCanceled():
                        return
                    progress.setValue(int(percent))
                    progress.setLabelText(f'Cargando lista de canales...\nCanales encontrados: {channels_count}')
                    QApplication.processEvents()
                
                self.playlist_manager.load_playlist(file_name, progress_callback=update_progress)
                progress.setValue(100)
                self.playlist_manager.save_last_playlist()
                
                # Desconectar señal existente si existe
                try:
                    self.group_filter.currentTextChanged.disconnect(self.update_channel_list)
                except:
                    pass
                
                # Actualizar filtro de grupos
                self.group_filter.clear()
                self.group_filter.addItem('Todos los grupos')
                self.group_filter.addItems(sorted(self.playlist_manager.groups))
                
                # Mostrar canales
                self.update_channel_list('Todos los grupos')
                
                # Conectar el cambio de grupo
                self.group_filter.currentTextChanged.connect(self.update_channel_list)
                
                QMessageBox.information(self, 'Lista Cargada', 
                                      f'Se cargaron {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos.')
            except Exception as e:
                # Mostrar un mensaje de error detallado al usuario
                error_message = f"Error al cargar la lista: {str(e)}"
                print(error_message)  # Imprimir en consola para depuración
                QMessageBox.critical(self, "Error de carga", 
                                   error_message + "\n\nRevise el formato de la lista y asegúrese de que sea un archivo M3U válido.")
    
    def update_channel_list(self, group: str):
        self.channel_list.clear()
        channels = self.playlist_manager.get_channels_by_group(group)
        for channel in channels:
            item = QListWidgetItem()
            # Crear un widget personalizado para cada canal
            channel_widget = QWidget()
            layout = QHBoxLayout(channel_widget)
            
            # Nombre del canal
            name_label = QLabel(channel.name)
            layout.addWidget(name_label)
            
            # Estado del canal
            status_label = QLabel()
            if channel.status == 'online':
                status_label.setStyleSheet('color: green;')
                status_label.setText('✓ Online')
            elif channel.status == 'slow':
                status_label.setStyleSheet('color: orange;')
                status_label.setText('⚠ Lento')
            elif channel.status == 'offline':
                status_label.setStyleSheet('color: red;')
                status_label.setText('✗ Offline')
            else:
                status_label.setText('? Desconocido')
            
            layout.addWidget(status_label)
            layout.addStretch()
            
            # Tiempo de respuesta si está disponible
            if channel.response_time is not None:
                response_label = QLabel(f'{channel.response_time:.2f}s')
                response_label.setStyleSheet('color: gray;')
                layout.addWidget(response_label)
            
            channel_widget.setLayout(layout)
            
            # Configurar el item
            item.setSizeHint(channel_widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, channel)
            self.channel_list.addItem(item)
            self.channel_list.setItemWidget(item, channel_widget)
            
    def play_channel(self, item):
        channel: Channel = item.data(Qt.ItemDataRole.UserRole)
        if channel and channel.url:
            try:
                # Detener reproducción actual si existe
                if self.player.is_playing():
                    self.player.stop()
                
                # Crear nuevo medio
                media = self.instance.media_new(channel.url)
                self.player.set_media(media)
                
                # Configurar el widget de video
                if sys.platform == 'win32':
                    self.player.set_hwnd(int(self.video_widget.winId()))
                
                # Iniciar reproducción
                self.player.play()
                
                # Programar una verificación de pistas de audio después de que el medio se haya cargado
                QTimer.singleShot(2000, self.check_audio_tracks)
                
                print(f"Reproduciendo canal: {channel.name}")
            except Exception as e:
                print(f"Error al reproducir canal: {e}")
                QMessageBox.warning(self, "Error de Reproducción", 
                                  f"No se pudo reproducir el canal {channel.name}:\n{str(e)}")
    
    def check_audio_tracks(self):
        """Verifica las pistas de audio disponibles después de cargar un medio"""
        try:
            if not self.player.get_media():
                return
                
            # Obtener información de pistas de audio
            audio_tracks_count = self.player.audio_get_track_count()
            current_track = self.player.audio_get_track()
            
            print(f"Pistas de audio detectadas: {audio_tracks_count}, pista actual: {current_track}")
            
            # Si hay múltiples pistas de audio, mostrar notificación
            if audio_tracks_count > 1:
                tracks_info = "Este canal tiene múltiples pistas de audio disponibles.\n"
                tracks_info += "Haga clic derecho sobre el video para cambiar el idioma del audio."
                
                QMessageBox.information(self, "Múltiples Pistas de Audio", tracks_info)
        except Exception as e:
            print(f"Error al verificar pistas de audio: {e}")
            # No mostrar mensaje de error al usuario para no interrumpir la experiencia
        
    def toggle_fullscreen(self):
        try:
            if self.isFullScreen():
                # Salir del modo pantalla completa
                self.showNormal()
                # Restaurar banderas de ventana normales
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.FramelessWindowHint)
                self.show()
                
                if self.player:
                    try:
                        self.player.set_fullscreen(False)
                    except Exception as vlc_error:
                        print(f"Error al cambiar modo VLC: {vlc_error}")
                    # Restaurar el layout normal
                    self.centralWidget().layout().setContentsMargins(11, 11, 11, 11)
                    self.video_widget.setFocus()
                
                # Restaurar visibilidad del panel lateral
                self.is_fullscreen_mode = False
                self.sidebar_visible = True
                self.sidebar.show()
            else:
                # Entrar en modo pantalla completa
                # Primero cambiar banderas de ventana
                self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
                self.showFullScreen()
                
                if self.player:
                    try:
                        self.player.set_fullscreen(True)
                    except Exception as vlc_error:
                        print(f"Error al cambiar modo VLC: {vlc_error}")
                    # Eliminar márgenes en pantalla completa
                    self.centralWidget().layout().setContentsMargins(0, 0, 0, 0)
                    self.video_widget.setFocus()
                
                # Ocultar panel lateral en pantalla completa
                self.is_fullscreen_mode = True
                self.sidebar_visible = False
                self.sidebar.hide()
        except Exception as e:
            print(f"Error al cambiar modo de pantalla: {e}")
            # Intentar restaurar a un estado conocido
            try:
                self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.FramelessWindowHint)
                self.showNormal()
                self.centralWidget().layout().setContentsMargins(11, 11, 11, 11)
                self.is_fullscreen_mode = False
                self.sidebar_visible = True
                self.sidebar.show()
            except Exception as restore_error:
                print(f"Error al restaurar ventana: {restore_error}")
                # Último recurso
                self.close()
                QMessageBox.critical(None, "Error Crítico", 
                                   "La aplicación encontró un error grave al cambiar el modo de pantalla y necesita reiniciarse.")

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.Type.KeyPress:
                # El evento ya es un QKeyEvent, no necesitamos convertirlo
                if event.key() == Qt.Key.Key_F11 or \
                   (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
                    self.toggle_fullscreen()
                    return True
                elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
                    self.toggle_fullscreen()
                    return True
            return super().eventFilter(obj, event)
        except Exception as e:
            print(f"Error en el manejo de eventos: {e}")
            return False

    async def check_channels_async(self):
        progress = QProgressDialog('Verificando canales...', 'Cancelar', 0, len(self.playlist_manager.channels), self)
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(500)  # Mostrar diálogo solo si tarda más de 500ms
        progress.setValue(0)
        progress.show()
        
        try:
            # Configurar una función de actualización para el progreso
            completed_count = 0
            
            # Modificar el método check_all_channels para que actualice el progreso
            original_check_channel = self.playlist_manager.check_channel
            
            async def wrapped_check_channel(channel):
                nonlocal completed_count
                await original_check_channel(channel)
                completed_count += 1
                progress.setValue(completed_count)
                # Procesar eventos para mantener la UI responsiva
                QApplication.processEvents()
                
            # Reemplazar temporalmente el método
            self.playlist_manager.check_channel = wrapped_check_channel
            
            try:
                # Ejecutar verificación con el método modificado
                await self.playlist_manager.check_all_channels()
            finally:
                # Restaurar el método original
                self.playlist_manager.check_channel = original_check_channel
            
        except asyncio.CancelledError:
            print("Verificación de canales cancelada por el usuario")
            QMessageBox.information(self, 'Operación Cancelada', 'La verificación de canales fue cancelada')
        except Exception as e:
            print(f"Error durante la verificación de canales: {e}")
            QMessageBox.warning(self, 'Error de Verificación', 
                              f'Ocurrió un error durante la verificación de canales: {str(e)}')
        finally:
            progress.setValue(len(self.playlist_manager.channels))
            progress.close()
            self.update_channel_list(self.group_filter.currentText())
            
            # Mostrar resumen de verificación
            online_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'online')
            slow_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'slow')
            offline_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'offline')
            
            QMessageBox.information(self, 'Verificación Completada', 
                                  f'Resumen de verificación:\n'
                                  f'- Canales en línea: {online_count}\n'
                                  f'- Canales lentos: {slow_count}\n'
                                  f'- Canales fuera de línea: {offline_count}\n'
                                  f'- Total verificado: {len(self.playlist_manager.channels)}')
    
    def check_channels(self):
        try:
            # Configurar una política de manejo de eventos para evitar errores de conexión
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(self.check_channels_async())
        except Exception as e:
            print(f"Error al ejecutar verificación de canales: {e}")
            QMessageBox.warning(self, 'Error', f'No se pudo completar la verificación: {str(e)}')
    
    def save_working_channels(self):
        file_name, _ = QFileDialog.getSaveFileName(self, 'Guardar Canales Funcionales',
                                                '', 'M3U Files (*.m3u);;M3U8 Files (*.m3u8)')
        if file_name:
            self.playlist_manager.save_working_channels(file_name)
            
    def download_playlist(self):
        url, ok = QInputDialog.getText(self, 'Descargar Lista M3U', 
                                     'Ingrese la URL de la lista M3U:')
        if ok and url:
            # Mostrar diálogo de progreso
            progress = QProgressDialog('Descargando lista...', 'Cancelar', 0, 0, self)
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()
            
            try:
                # Configurar una política de manejo de eventos para evitar errores de conexión
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                print(f"Iniciando descarga desde URL: {url}")
                # Descargar la lista con manejo de excepciones mejorado
                success, message, file_path = self.playlist_manager.download_playlist_from_url_sync(url)
                
                if success:
                    try:
                        print(f"Descarga exitosa, cargando lista desde: {file_path}")
                        # Cargar la lista descargada
                        self.playlist_manager.load_playlist(file_path)
                        self.playlist_manager.save_last_playlist()
                        
                        # Actualizar filtro de grupos
                        self.group_filter.clear()
                        self.group_filter.addItem('Todos los grupos')
                        self.group_filter.addItems(self.playlist_manager.groups)
                        
                        # Mostrar canales
                        self.update_channel_list('Todos los grupos')
                        
                        # Conectar el cambio de grupo
                        self.group_filter.currentTextChanged.connect(self.update_channel_list)
                        
                        QMessageBox.information(self, 'Descarga Completada', 
                                              f'Lista descargada correctamente y guardada en: {file_path}\n'
                                              f'Se cargaron {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos.')
                    except Exception as e:
                        print(f"Error al cargar la lista descargada: {e}")
                        QMessageBox.warning(self, 'Error al Cargar', 
                                          f'La lista se descargó pero no se pudo cargar:\n{str(e)}\n\n'
                                          f'Archivo: {file_path}')
                else:
                    print(f"Error en la descarga: {message}")
                    QMessageBox.warning(self, 'Error de Descarga', 
                                      f'{message}\n\nVerifique que la URL sea correcta y que el servidor esté disponible.')
            except Exception as e:
                print(f"Error inesperado durante la descarga: {e}")
                QMessageBox.critical(self, 'Error Crítico', 
                                   f'Ocurrió un error inesperado: {str(e)}')
            finally:
                progress.close()
            
    def check_mouse_position(self):
        """Verifica la posición del ratón para mostrar/ocultar el panel lateral en modo pantalla completa"""
        if not self.is_fullscreen_mode:
            return
            
        cursor_pos = QCursor.pos()
        window_pos = self.mapToGlobal(QPoint(0, 0))
        relative_x = cursor_pos.x() - window_pos.x()
        
        if relative_x <= self.sidebar_hover_margin and not self.sidebar_visible:
            # El cursor está cerca del borde izquierdo, mostrar el panel
            self.sidebar.show()
            self.sidebar_visible = True
        elif relative_x > self.sidebar.width() + 10 and self.sidebar_visible:
            # El cursor está lejos del panel, ocultarlo
            self.sidebar.hide()
            self.sidebar_visible = False

    def show_video_context_menu(self, position):
        """Muestra un menú contextual para el widget de video"""
        # Solo mostrar el menú si hay un medio cargado
        if not self.player.get_media():
            return
            
        # Crear el menú contextual
        context_menu = QMenu(self)
        
        # Añadir opción para pistas de audio
        audio_menu = QMenu("Pistas de Audio", self)
        context_menu.addMenu(audio_menu)
        
        try:
            # Obtener el número de pistas de audio disponibles
            audio_tracks_count = self.player.audio_get_track_count()
            current_track = self.player.audio_get_track()
            
            print(f"Pistas de audio disponibles: {audio_tracks_count}, pista actual: {current_track}")
            
            if audio_tracks_count > 0:
                # Añadir cada pista de audio al menú
                for i in range(audio_tracks_count):
                    try:
                        track_id = self.player.audio_get_track_id(i)
                        track_description = self.player.audio_get_track_description(i)
                        
                        # Extraer solo la descripción de la pista (puede variar según la versión de VLC)
                        track_name = f"Pista {i+1}"
                        if track_description:
                            if isinstance(track_description, tuple) and len(track_description) > 1:
                                # En algunas versiones de VLC, la descripción es una tupla (id, nombre)
                                track_name = track_description[1].decode('utf-8', errors='ignore')
                            elif isinstance(track_description, bytes):
                                # En otras versiones puede ser directamente bytes
                                track_name = track_description.decode('utf-8', errors='ignore')
                            elif isinstance(track_description, str):
                                # O directamente un string
                                track_name = track_description
                        
                        print(f"Pista {i}: ID={track_id}, Nombre={track_name}")
                        
                        action = QAction(track_name, self)
                        action.setCheckable(True)
                        action.setChecked(track_id == current_track)
                        
                        # Usar una función de fábrica para capturar correctamente el valor de track_id
                        def create_track_handler(tid):
                            return lambda checked: self.change_audio_track(tid)
                            
                        action.triggered.connect(create_track_handler(track_id))
                        audio_menu.addAction(action)
                    except Exception as track_error:
                        print(f"Error al procesar pista {i}: {track_error}")
            else:
                # Si no hay pistas de audio disponibles
                no_tracks_action = QAction("No hay pistas disponibles", self)
                no_tracks_action.setEnabled(False)
                audio_menu.addAction(no_tracks_action)
                
            # Añadir opción para refrescar las pistas de audio
            audio_menu.addSeparator()
            refresh_action = QAction("Refrescar pistas de audio", self)
            refresh_action.triggered.connect(lambda: self.refresh_audio_tracks())
            audio_menu.addAction(refresh_action)
            
        except Exception as e:
            print(f"Error al obtener pistas de audio: {e}")
            error_action = QAction(f"Error: {str(e)}", self)
            error_action.setEnabled(False)
            audio_menu.addAction(error_action)
        
        # Mostrar el menú en la posición del cursor
        context_menu.exec(self.video_widget.mapToGlobal(position))
    
    def refresh_audio_tracks(self):
        """Refresca la información de pistas de audio disponibles"""
        try:
            if not self.player.get_media():
                QMessageBox.information(self, "Información", 
                                      "No hay medio cargado para refrescar las pistas de audio.")
                return
                
            # Forzar a VLC a recargar las pistas de audio
            current_time = self.player.get_time()
            was_playing = self.player.is_playing()
            
            # Pausar si está reproduciendo
            if was_playing:
                self.player.pause()
            
            # Esperar un momento para que VLC actualice la información
            QTimer.singleShot(500, lambda: self.complete_refresh(current_time, was_playing))
            
            print("Refrescando pistas de audio...")
        except Exception as e:
            print(f"Error al refrescar pistas de audio: {e}")
            QMessageBox.warning(self, "Error", 
                              f"No se pudieron refrescar las pistas de audio: {str(e)}")
    
    def complete_refresh(self, time_pos, was_playing):
        """Completa el proceso de refrescar las pistas de audio"""
        try:
            # Restaurar posición de tiempo
            self.player.set_time(time_pos)
            
            # Continuar reproducción si estaba reproduciendo
            if was_playing:
                self.player.play()
            
            # Mostrar información de pistas disponibles
            audio_tracks_count = self.player.audio_get_track_count()
            current_track = self.player.audio_get_track()
            
            tracks_info = f"Pistas de audio disponibles: {audio_tracks_count}\n"
            tracks_info += f"Pista actual: {current_track}\n\n"
            
            if audio_tracks_count > 0:
                tracks_info += "Pistas disponibles:\n"
                for i in range(audio_tracks_count):
                    try:
                        track_id = self.player.audio_get_track_id(i)
                        track_description = self.player.audio_get_track_description(i)
                        
                        track_name = f"Pista {i+1}"
                        if track_description:
                            if isinstance(track_description, tuple) and len(track_description) > 1:
                                track_name = track_description[1].decode('utf-8', errors='ignore')
                            elif isinstance(track_description, bytes):
                                track_name = track_description.decode('utf-8', errors='ignore')
                            elif isinstance(track_description, str):
                                track_name = track_description
                        
                        tracks_info += f"- {track_name} (ID: {track_id})\n"
                    except Exception as e:
                        tracks_info += f"- Error en pista {i}: {str(e)}\n"
            
            print(tracks_info)
            QMessageBox.information(self, "Pistas de Audio", tracks_info)
        except Exception as e:
            print(f"Error al completar el refresco de pistas: {e}")
    
    def change_audio_track(self, track_id):
        """Cambia la pista de audio actual"""
        try:
            # Verificar que el reproductor esté activo y tenga un medio cargado
            if not self.player.get_media():
                print("No hay medio cargado para cambiar la pista de audio")
                return False
                
            # Intentar cambiar la pista de audio
            result = self.player.audio_set_track(track_id)
            
            if result:
                print(f"Pista de audio cambiada a ID: {track_id}")
                # Mostrar un mensaje temporal en la interfaz
                current_track_index = -1
                for i in range(self.player.audio_get_track_count()):
                    if self.player.audio_get_track_id(i) == track_id:
                        current_track_index = i
                        break
                        
                if current_track_index >= 0:
                    track_description = self.player.audio_get_track_description(current_track_index)
                    track_name = f"Pista {current_track_index+1}"
                    if track_description and isinstance(track_description, tuple) and len(track_description) > 1:
                        track_name = track_description[1].decode('utf-8', errors='ignore')
                    
                    QMessageBox.information(self, "Cambio de Audio", 
                                         f"Pista de audio cambiada a: {track_name}", 
                                         QMessageBox.StandardButton.Ok)
                return True
            else:
                print(f"Error al cambiar la pista de audio a ID: {track_id}")
                return False
        except Exception as e:
            print(f"Excepción al cambiar pista de audio: {e}")
            return False

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = TVIPPlayer()
    player.show()
    sys.exit(app.exec())