import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QListWidget, QLabel, QPushButton,
                             QComboBox, QFileDialog, QListWidgetItem, QSizePolicy,
                             QProgressDialog, QInputDialog, QMessageBox, QMenu, QGridLayout)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction, QIcon
import vlc
import asyncio
from playlist_manager import PlaylistManager, Channel

class TVIPPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TV IP Player')
        self.setGeometry(100, 100, 1200, 700)
        self.setMinimumSize(900, 600)
        self.installEventFilter(self)
        
        # Variables para control de panel lateral
        self.sidebar_visible = True
        self.is_fullscreen_mode = False
        self.sidebar_hover_margin = 20
        self.sidebar_position = "right"  # Nueva variable para controlar la posición del sidebar (right o left)
        self.mouse_check_timer = QTimer(self)
        self.mouse_check_timer.timeout.connect(self.check_mouse_position)
        self.mouse_check_timer.start(100)
        
        # Variables para control de video
        self.current_audio_track = 0
        self.audio_tracks = []
        self.current_aspect_ratio = 'auto'
        self.current_scale = 1.0
        
        # Inicializar el gestor de listas
        self.playlist_manager = PlaylistManager()
        
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
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Panel lateral para lista de canales
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar.setMinimumWidth(280)
        self.sidebar.setMaximumWidth(350)
        
        # Filtro por grupos
        self.group_filter = QComboBox()
        self.group_filter.addItem('Todos los grupos')
        sidebar_layout.addWidget(QLabel('Filtrar por grupo:'))
        sidebar_layout.addWidget(self.group_filter)
        
        # Lista de canales
        self.channel_list = QListWidget()
        sidebar_layout.addWidget(QLabel('Canales:'))
        sidebar_layout.addWidget(self.channel_list)
        
        # Botones de control
        buttons_grid = QGridLayout()
        
        # Primera fila de botones
        load_button = QPushButton('Cargar Lista M3U')
        load_button.clicked.connect(self.load_playlist)
        load_button.setMinimumWidth(140)
        download_button = QPushButton('Descargar Lista')
        download_button.clicked.connect(self.download_playlist)
        download_button.setMinimumWidth(140)
        
        buttons_grid.addWidget(load_button, 0, 0)
        buttons_grid.addWidget(download_button, 0, 1)
        
        # Segunda fila de botones
        check_button = QPushButton('Verificar Canales')
        check_button.clicked.connect(self.check_channels)
        check_button.setMinimumWidth(140)
        save_working_button = QPushButton('Guardar Canales Funcionales')
        save_working_button.clicked.connect(self.save_working_channels)
        save_working_button.setMinimumWidth(140)
        
        buttons_grid.addWidget(check_button, 1, 0)
        buttons_grid.addWidget(save_working_button, 1, 1)
        
        # Botón rojo en tercera fila centrada
        process_button = QPushButton('Procesar y Filtrar Canales')
        process_button.setMinimumWidth(140)
        process_button.setStyleSheet('background-color: #C62828; color: white; font-weight: bold;')
        process_button.clicked.connect(self.process_and_filter_channels_background)
        buttons_grid.addWidget(process_button, 2, 0, 1, 2)
        
        # Agregar el grid al layout principal
        buttons_container = QWidget()
        buttons_container.setLayout(buttons_grid)
        sidebar_layout.addWidget(buttons_container)
        
        # Área de reproducción
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0, 0, 0, 0)
        self.video_layout.setSpacing(0)
        layout.addWidget(self.video_container)
        
        # Widget para el video
        self.video_widget = QWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.video_widget.setMouseTracking(True)
        self.video_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.video_widget.customContextMenuRequested.connect(self.show_video_context_menu)
        self.video_layout.addWidget(self.video_widget)
        
        # Configurar el reproductor VLC para usar el widget de video
        if sys.platform.startswith('win'):
            self.player.set_hwnd(int(self.video_widget.winId()))
        elif sys.platform.startswith('linux'):
            self.player.set_xwindow(self.video_widget.winId())
        elif sys.platform.startswith('darwin'):
            self.player.set_nsobject(int(self.video_widget.winId()))
        
        # Overlay transparente para capturar clic derecho
        self.overlay_widget = QWidget(self.video_widget)
        self.overlay_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.overlay_widget.setStyleSheet("background: transparent;")
        self.overlay_widget.setMouseTracking(True)
        self.overlay_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.DefaultContextMenu)
        self.overlay_widget.show()
        self.overlay_widget.resize(self.video_widget.size())
        self.overlay_widget.installEventFilter(self)

        # Botón flotante para mostrar menú contextual sobre el video (hijo de la ventana principal)
        self.menu_button = QPushButton(self)
        self.menu_button.setIcon(QIcon.fromTheme('application-menu'))
        self.menu_button.setStyleSheet('''
            QPushButton {
                background: rgba(255,255,255,0.1);
                border: none;
                border-radius: 12px;
                padding: 2px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.4);
            }
        ''')
        self.menu_button.setFixedSize(24, 24)
        self.menu_button.setToolTip('Mostrar menú de video')
        self.menu_button.clicked.connect(lambda: self.show_video_context_menu(self.menu_button.rect().bottomRight()))
        self.menu_button.raise_()
        self.menu_button.show()
        self.update_menu_button_position()
        
        if self.sidebar_position == "right":
            layout.addWidget(self.sidebar)
        else:
            layout.addWidget(self.sidebar, 0, 0)
        
        # Conectar eventos de canales
        self.channel_list.itemDoubleClicked.connect(self.play_channel)
        self.group_filter.currentTextChanged.connect(self.update_channel_list)
        
        # Timer para verificar las pistas de audio disponibles
        self.audio_check_timer = QTimer(self)
        self.audio_check_timer.timeout.connect(self.check_audio_tracks)
        self.audio_check_timer.start(1000)  # Verificar cada segundo
        
        # Instalar event filter global para clic derecho sobre video (VLC)
        QApplication.instance().installEventFilter(self)

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
        try:
            channel = item.data(Qt.ItemDataRole.UserRole)
            if channel and channel.url:
                print(f"Iniciando reproducción de canal. Estado actual: isFullScreen={self.isFullScreen()}, is_fullscreen_mode={self.is_fullscreen_mode}")
                
                # Asegurar que estamos en modo ventana normal antes de reproducir
                if self.isFullScreen():
                    print("Forzando salida de pantalla completa antes de reproducir")
                    self.showNormal()
                    if hasattr(self, 'normal_geometry'):
                        self.setGeometry(self.normal_geometry)
                    self.is_fullscreen_mode = False
                    if hasattr(self, 'sidebar'):
                        self.sidebar.show()
                
                # Configurar opciones de reproducción específicas para este medio
                media = self.instance.media_new(channel.url)
                media.add_option('avcodec-hw=none')  # Deshabilitar decodificación por hardware
                media.add_option('no-direct3d11-hw-blending')  # Deshabilitar mezcla por hardware
                media.add_option('no-direct3d11')  # Deshabilitar Direct3D11
                media.add_option('no-fullscreen')  # Evitar pantalla completa automática
                media.add_option('embedded-video')  # Forzar video embebido
                
                # Asegurar que el reproductor esté configurado para usar el widget de video
                if sys.platform.startswith('win'):
                    self.player.set_hwnd(int(self.video_widget.winId()))
                elif sys.platform.startswith('linux'):
                    self.player.set_xwindow(self.video_widget.winId())
                elif sys.platform.startswith('darwin'):
                    self.player.set_nsobject(int(self.video_widget.winId()))
                
                self.player.set_media(media)
                self.player.play()
                
                # Verificar nuevamente después de iniciar la reproducción
                print(f"Después de iniciar reproducción: isFullScreen={self.isFullScreen()}, is_fullscreen_mode={self.is_fullscreen_mode}")
                
                # Programar una verificación adicional después de un breve retraso
                QTimer.singleShot(100, self._check_fullscreen_after_play)
                
        except Exception as e:
            print(f"Error al reproducir canal: {e}")
            QMessageBox.warning(self, "Error de Reproducción", 
                              f"No se pudo reproducir el canal: {str(e)}")

    def check_audio_tracks(self):
        if not self.player.is_playing():
            return
        
        media = self.player.get_media()
        if not media:
            return
        
        # Obtener la lista de pistas de audio
        tracks = []
        for i in range(self.player.audio_get_track_count()):
            track_description = self.player.audio_get_track_description()[i]
            if track_description:
                tracks.append(track_description)
        
        # Actualizar el botón si hay múltiples pistas
        if len(tracks) > 1:
            current_track = self.player.audio_get_track()
            current_track_info = next((t for t in tracks if t[0] == current_track), None)
            # if current_track_info:
            #     print(f"Pista de audio actual: {current_track_info[1].decode()}")
            self.audio_tracks = tracks
        else:
            self.audio_tracks = []

    def toggle_fullscreen(self):
        """Alterna entre modo pantalla completa y ventana normal"""
        print(f"toggle_fullscreen llamado. is_fullscreen_mode={self.is_fullscreen_mode}, isFullScreen()={self.isFullScreen()}")
        if not self.isFullScreen():
            self.normal_geometry = self.geometry()
            if hasattr(self, 'sidebar'):
                self.sidebar.hide()
                self.sidebar_visible = False
            self.showFullScreen()
            self.is_fullscreen_mode = True
            print("Entrando a pantalla completa")
            if hasattr(self, 'video_widget'):
                self.video_widget.setFocus()
        else:
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            print("Saliendo de pantalla completa")
            if hasattr(self, 'sidebar'):
                self.sidebar.show()
                self.sidebar_visible = True

    def eventFilter(self, obj, event):
        try:
            from PyQt6.QtCore import Qt as QtCoreQt, QEvent
            # Mantener overlay del tamaño del video_widget
            if obj == self.video_widget and event.type() == QEvent.Type.Resize:
                self.overlay_widget.resize(self.video_widget.size())
                self.update_menu_button_position()
            if obj == self.overlay_widget and event.type() == QEvent.Type.Resize:
                self.update_menu_button_position()
            # Captura global de clic derecho
            if event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == QtCoreQt.MouseButton.RightButton:
                    # Verifica si el cursor está sobre el área de video
                    global_pos = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else event.globalPos()
                    video_rect = self.video_widget.geometry()
                    video_top_left = self.video_widget.mapToGlobal(video_rect.topLeft())
                    video_bottom_right = self.video_widget.mapToGlobal(video_rect.bottomRight())
                    x, y = global_pos.x(), global_pos.y()
                    if (video_top_left.x() <= x <= video_bottom_right.x() and
                        video_top_left.y() <= y <= video_bottom_right.y()):
                        # Mostrar menú contextual en la posición relativa al widget de video
                        rel_pos = self.video_widget.mapFromGlobal(global_pos)
                        self.show_video_context_menu(rel_pos)
                        return True
            if obj == self.overlay_widget and event.type() == QEvent.Type.MouseButtonPress:
                if event.button() == QtCoreQt.MouseButton.RightButton:
                    self.show_video_context_menu(event.pos())
                    return True
            # El evento ya es un QKeyEvent, no necesitamos convertirlo
            if event.type() == QEvent.Type.KeyPress:
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
        
        # Variable para rastrear si la operación fue cancelada
        was_cancelled = False
        
        try:
            # Configurar una función de actualización para el progreso
            completed_count = 0
            
            # Modificar el método check_all_channels para que actualice el progreso
            original_check_channel = self.playlist_manager.check_channel
            
            async def wrapped_check_channel(channel):
                nonlocal completed_count
                try:
                    await original_check_channel(channel)
                finally:
                    completed_count += 1
                    progress.setValue(completed_count)
                    # Procesar eventos para mantener la UI responsiva
                    QApplication.processEvents()
                    
                    # Verificar si el usuario canceló la operación
                    if progress.wasCanceled():
                        raise asyncio.CancelledError("Usuario canceló la operación")
            
            # Reemplazar temporalmente el método
            self.playlist_manager.check_channel = wrapped_check_channel
            
            try:
                # Ejecutar verificación con el método modificado
                await self.playlist_manager.check_all_channels()
            finally:
                # Restaurar el método original
                self.playlist_manager.check_channel = original_check_channel
        
        except asyncio.CancelledError:
            was_cancelled = True
            print("Verificación de canales cancelada por el usuario")
        except Exception as e:
            print(f"Error al ejecutar verificación de canales: {str(e)}")
            QMessageBox.warning(self, 'Error de Verificación', 
                              f'Ocurrió un error durante la verificación de canales:\n{str(e)}')
        finally:
            progress.setValue(len(self.playlist_manager.channels))
            progress.close()
            
            # Actualizar la lista solo si no fue cancelada
            if not was_cancelled:
                self.update_channel_list(self.group_filter.currentText())
                
                # Mostrar resumen de verificación
                online_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'online')
                slow_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'slow')
                offline_count = sum(1 for ch in self.playlist_manager.channels if ch.status == 'offline')
                
                if was_cancelled:
                    message = "La verificación fue cancelada.\n\nResultados parciales:"
                else:
                    message = "Verificación completada.\n\nResultados:"
                
                QMessageBox.information(self, 'Verificación de Canales', 
                                      f'{message}\n'
                                      f'- Canales en línea: {online_count}\n'
                                      f'- Canales lentos: {slow_count}\n'
                                      f'- Canales fuera de línea: {offline_count}\n'
                                      f'- Total verificado: {completed_count}')

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
        window_width = self.width()
        relative_x = cursor_pos.x() - window_pos.x()
        
        # Verificar si el cursor está cerca del borde derecho
        if relative_x >= (window_width - self.sidebar_hover_margin) and not self.sidebar_visible:
            # El cursor está cerca del borde derecho, mostrar el panel
            self.sidebar.show()
            self.sidebar_visible = True
            self.sidebar_position = "right"
        # Verificar si el cursor está lejos del panel cuando está visible
        elif self.sidebar_visible and self.sidebar_position == "right":
            # Si está a la derecha, verificar si el cursor está lejos del borde derecho
            if relative_x < (window_width - self.sidebar.width() - 10):
                self.sidebar.hide()
                self.sidebar_visible = False

    def show_video_context_menu(self, position):
        print("MENÚ CONTEXTUAL INVOCADO", position)
        context_menu = QMenu(self)
        # Acción de pantalla completa
        fullscreen_action = QAction('Pantalla Completa', self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        context_menu.addAction(fullscreen_action)
        
        # Opciones de cambio de tamaño de video
        scale_menu = QMenu('Escala de Video', self)
        scales = {
            'Ajuste Original (1.0x)': 1.0,
            'Ajuste a Ventana (0.5x)': 0.5,
            'Ajuste Doble (2.0x)': 2.0
        }
        for name, scale in scales.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(self.current_scale == scale)
            def create_scale_handler(s):
                return lambda: self.set_scale_mode(s)
            action.triggered.connect(create_scale_handler(scale))
            scale_menu.addAction(action)
        context_menu.addMenu(scale_menu)
        
        # Opciones de relación de aspecto
        aspect_menu = QMenu('Relación de Aspecto', self)
        aspect_ratios = {
            'Auto': '',
            '16:9': '16:9',
            '4:3': '4:3',
            '1:1': '1:1',
            '16:10': '16:10',
            '2.35:1 (Cinemascope)': '2.35:1',
            '2.21:1 (Panavision)': '221:100',
            '1.85:1 (Cine)': '185:100',
            '5:4': '5:4',
            '5:3': '5:3',
            '3:2': '3:2'
        }
        for name, ratio in aspect_ratios.items():
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(self.current_aspect_ratio == ratio)
            def create_ratio_handler(r):
                return lambda: self.set_aspect_ratio(r)
            action.triggered.connect(create_ratio_handler(ratio))
            aspect_menu.addAction(action)
        context_menu.addMenu(aspect_menu)

        # Opciones de pistas de audio (usando audio_get_track_description)
        if self.player and self.player.get_media():
            desc_list = self.player.audio_get_track_description()
            if desc_list and len(desc_list) > 1:
                audio_menu = QMenu('Pistas de Audio', self)
                current_track = self.player.audio_get_track()
                for desc in desc_list:
                    track_id, name = desc
                    if isinstance(name, bytes):
                        track_name = name.decode('utf-8', errors='ignore')
                    elif isinstance(name, str):
                        track_name = name
                    else:
                        track_name = f"Pista {track_id}"
                    action = QAction(track_name, self)
                    action.setCheckable(True)
                    action.setChecked(track_id == current_track)
                    def create_track_handler(tid):
                        return lambda: self.change_audio_track(tid)
                    action.triggered.connect(create_track_handler(track_id))
                    audio_menu.addAction(action)
                context_menu.addMenu(audio_menu)
        
        # Mostrar el menú en la posición global del cursor
        global_pos = self.video_widget.mapToGlobal(position)
        context_menu.exec(global_pos)

    def set_scale_mode(self, scale):
        try:
            scale = float(scale)
            self.player.video_set_scale(scale)
            self.current_scale = scale
            print(f"Escala de video cambiada a: {scale}")
        except Exception as e:
            print(f"Error al cambiar la escala del video: {e}")
    
    def change_audio_track(self, track_id):
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

    def process_and_filter_channels_background(self):
        from PyQt6.QtWidgets import QFileDialog
        file_name, _ = QFileDialog.getOpenFileName(self, 'Selecciona una lista M3U para procesar', '', 'M3U Files (*.m3u *.m3u8)')
        if file_name:
            import threading
            thread = threading.Thread(target=self.process_and_filter_channels, args=(file_name,), daemon=True)
            thread.start()

    def process_and_filter_channels(self, file_path):
        # Procesar la lista seleccionada (no la actual), sin afectar la UI
        import asyncio
        import tempfile
        from datetime import datetime
        from playlist_manager import PlaylistManager
        # 1. Cargar la lista seleccionada en un PlaylistManager separado
        pm = PlaylistManager()
        try:
            pm.load_playlist(file_path)
        except Exception as e:
            print(f"Error al cargar la lista seleccionada: {e}")
            return
        # 2. Completar metadatos ya lo hace load_playlist
        # 3. Verificar canales (asyncio, en este hilo)
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(pm.check_all_channels())
        except Exception as e:
            print(f"Error en verificación de canales: {e}")
        finally:
            if loop:
                loop.close()
        # 4. Guardar solo los funcionales
        working_channels = [ch for ch in pm.channels if ch.status in ['online', 'slow']]
        if working_channels:
            temp_dir = tempfile.gettempdir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            temp_file = os.path.join(temp_dir, f"canales_funcionales_{timestamp}.m3u")
            pm.save_m3u_playlist(temp_file, working_channels)
            print(f"Lista funcional generada: {temp_file}")
        else:
            print("No hay canales funcionales tras el filtrado.")

    def update_menu_button_position(self):
        # Calcula la posición global del área de video y coloca el botón flotante
        video_rect = self.video_widget.geometry()
        video_top_left = self.video_widget.mapTo(self, video_rect.topLeft())
        
        # Colocar el botón en la esquina izquierda superior
        x = video_top_left.x() + 4
        y = video_top_left.y() + 4
        self.menu_button.move(x, y)

    def keyPressEvent(self, event):
        print(f"keyPressEvent: key={event.key()} esc={Qt.Key.Key_Escape} fullscreen={self.isFullScreen()} is_fullscreen_mode={self.is_fullscreen_mode}")
        # Asegura que los atajos funcionen incluso si el foco está en el botón flotante
        if event.key() == Qt.Key.Key_F11 or \
           (event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.AltModifier):
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Escape and self.isFullScreen():
            print("ESC detectado, intentando salir de pantalla completa")
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_menu_button_position()
        if hasattr(self, 'overlay_widget'):
            self.overlay_widget.resize(self.video_widget.size())

    def _check_fullscreen_after_play(self):
        """Verifica y corrige el estado de pantalla completa después de iniciar la reproducción"""
        if self.isFullScreen():
            print("Detectado cambio a pantalla completa después de reproducir, forzando salida")
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            print("Forzado a modo ventana completado")
            
            # Programar otra verificación para asegurar que no vuelva a pantalla completa
            QTimer.singleShot(500, self._check_fullscreen_after_play)

    def _force_window_mode(self):
        """Método auxiliar para forzar el modo ventana"""
        print("Ejecutando _force_window_mode")
        if self.isFullScreen():
            self.showNormal()
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            self.is_fullscreen_mode = False
            if hasattr(self, 'sidebar'):
                self.sidebar.show()
            print("Forzado a modo ventana completado")

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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = TVIPPlayer()
    player.show()
    sys.exit(app.exec())