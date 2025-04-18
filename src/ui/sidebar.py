from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QLabel, QPushButton, QComboBox, QListWidgetItem, 
                            QSizePolicy, QProgressDialog, QInputDialog, 
                            QMessageBox, QGridLayout, QFileDialog)
from PyQt6.QtCore import Qt, QEvent, QTimer, QPoint
from PyQt6.QtGui import QKeyEvent, QColor, QCursor, QAction, QIcon

import asyncio
import os
import sys
from datetime import datetime

from src.core.playlist_manager import PlaylistManager, Channel
from src.core.media_player import MediaPlayer

class Sidebar(QWidget):
    """
    Panel lateral que contiene la lista de canales y los controles para
    gestionar las listas de reproducción.
    """
    
    def __init__(self, playlist_manager, media_player, parent=None):
        super().__init__(parent)
        self.playlist_manager = playlist_manager
        self.media_player = media_player
        self.parent_window = parent
        
        self.setMinimumWidth(280)
        self.setMaximumWidth(350)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de usuario del panel lateral"""
        sidebar_layout = QVBoxLayout(self)
        
        # Filtro por grupos
        self.group_filter = QComboBox()
        self.group_filter.addItem('Todos los grupos')
        self.group_filter.currentTextChanged.connect(self.on_group_changed)
        sidebar_layout.addWidget(QLabel('Filtrar por grupo:'))
        sidebar_layout.addWidget(self.group_filter)
        
        # Lista de canales
        self.channel_list = QListWidget()
        self.channel_list.itemDoubleClicked.connect(self.on_channel_selected)
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
    
    def on_group_changed(self, group):
        """Actualiza la lista de canales cuando se cambia el grupo seleccionado"""
        self.update_channel_list(group)
    
    def on_channel_selected(self, item):
        """Maneja la selección de un canal para reproducirlo"""
        self.play_channel(item)
    
    def update_channel_list(self, group: str):
        """Actualiza la lista de canales según el grupo seleccionado"""
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
                status_label.setText('●')
            elif channel.status == 'slow':
                status_label.setStyleSheet('color: orange;')
                status_label.setText('●')
            elif channel.status == 'offline':
                status_label.setStyleSheet('color: red;')
                status_label.setText('●')
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
        """Reproduce el canal seleccionado"""
        try:
            channel = item.data(Qt.ItemDataRole.UserRole)
            if channel and channel.url:
                print(f"Iniciando reproducción de canal: {channel.name}")
                
                # Asegurar que estamos en modo ventana normal antes de reproducir
                if self.parent_window and self.parent_window.isFullScreen():
                    print("Forzando salida de pantalla completa antes de reproducir")
                    self.parent_window.showNormal()
                    if hasattr(self.parent_window, 'normal_geometry'):
                        self.parent_window.setGeometry(self.parent_window.normal_geometry)
                    self.parent_window.is_fullscreen_mode = False
                    self.show()
                
                # Reproducir el canal
                self.media_player.play_media(channel.url)
                
                # Verificar nuevamente después de iniciar la reproducción
                if self.parent_window:
                    print(f"Después de iniciar reproducción: isFullScreen={self.parent_window.isFullScreen()}, is_fullscreen_mode={self.parent_window.is_fullscreen_mode}")
                
                    # Programar una verificación adicional después de un breve retraso
                    QTimer.singleShot(100, self.parent_window._check_fullscreen_after_play)
                
        except Exception as e:
            print(f"Error al reproducir canal: {e}")
            QMessageBox.warning(self, "Error de Reproducción", 
                              f"No se pudo reproducir el canal: {str(e)}")
    
    def load_playlist(self):
        """Carga una lista de reproducción desde un archivo"""
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
                    self.parent_window.update()
                
                # Cargar la lista
                self.playlist_manager.load_playlist(file_name, update_progress)
                
                # Actualizar la interfaz
                self.update_groups_combo()
                self.update_channel_list('Todos los grupos')
                
                # Mostrar mensaje de éxito
                QMessageBox.information(self, 'Lista Cargada', 
                                      f'Se cargaron {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos.')
            except Exception as e:
                # Mostrar un mensaje de error detallado al usuario
                error_message = f"Error al cargar la lista: {str(e)}"
                print(error_message)  # Imprimir en consola para depuración
                QMessageBox.critical(self, "Error de carga", 
                                   error_message + "\n\nRevise el formato de la lista y asegúrese de que sea un archivo M3U válido.")
    
    def load_last_playlist(self):
        """Carga la última lista de reproducción guardada"""
        if self.playlist_manager.channels:
            self.update_groups_combo()
            self.update_channel_list('Todos los grupos')
    
    def update_groups_combo(self):
        """Actualiza el combo de grupos con los grupos disponibles en la lista"""
        self.group_filter.clear()
        self.group_filter.addItem('Todos los grupos')
        for group in self.playlist_manager.groups:
            self.group_filter.addItem(group)
    
    def download_playlist(self):
        """Descarga una lista de reproducción desde una URL"""
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
                
                # Descargar la lista
                success, message, file_path = self.playlist_manager.download_playlist_from_url_sync(url)
                
                # Cerrar el diálogo de progreso
                progress.close()
                
                if success:
                    # Preguntar si cargar la lista descargada
                    response = QMessageBox.question(self, 'Lista Descargada', 
                                                 f'{message}\n\n¿Desea cargar la lista descargada?',
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                    
                    if response == QMessageBox.StandardButton.Yes:
                        # Crear diálogo de progreso para la carga
                        load_progress = QProgressDialog('Cargando lista descargada...', 'Cancelar', 0, 100, self)
                        load_progress.setWindowModality(Qt.WindowModality.WindowModal)
                        load_progress.setMinimumDuration(0)
                        load_progress.setAutoClose(True)
                        load_progress.setAutoReset(True)
                        
                        def update_load_progress(percent, channels_count):
                            if load_progress.wasCanceled():
                                return
                            load_progress.setValue(int(percent))
                            load_progress.setLabelText(f'Cargando lista descargada...\nCanales encontrados: {channels_count}')
                            self.parent_window.update()
                        
                        # Cargar la lista
                        self.playlist_manager.load_playlist(file_path, update_load_progress)
                        
                        # Actualizar la interfaz
                        self.update_groups_combo()
                        self.update_channel_list('Todos los grupos')
                        
                        # Mostrar mensaje de éxito
                        QMessageBox.information(self, 'Lista Cargada', 
                                              f'Se cargaron {len(self.playlist_manager.channels)} canales en {len(self.playlist_manager.groups)} grupos.')
                    else:
                        QMessageBox.information(self, 'Descarga Completada', 
                                              f'La lista ha sido descargada pero no cargada.\n'
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
    
    def check_channels(self):
        """Verifica el estado de todos los canales"""
        try:
            # Configurar una política de manejo de eventos para evitar errores de conexión
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(self.check_channels_async())
        except Exception as e:
            print(f"Error al ejecutar verificación de canales: {e}")
            QMessageBox.warning(self, 'Error', f'No se pudo completar la verificación: {str(e)}')
    
    async def check_channels_async(self):
        """Versión asíncrona de la verificación de canales"""
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
            
            # Guardar referencia al método original
            original_check_channel = self.playlist_manager.check_channel
            
            # Crear una función envoltorio que actualiza el progreso
            async def wrapped_check_channel(channel):
                nonlocal completed_count
                try:
                    await original_check_channel(channel)
                finally:
                    completed_count += 1
                    progress.setValue(completed_count)
                    # Procesar eventos para mantener la UI responsiva
                    self.parent_window.update()
                    
                    # Verificar si el usuario canceló la operación
                    if progress.wasCanceled():
                        raise asyncio.CancelledError("Usuario canceló la operación")
            
            # Crear tareas para verificar todos los canales
            tasks = []
            for channel in self.playlist_manager.channels:
                task = asyncio.create_task(wrapped_check_channel(channel))
                tasks.append(task)
                
            # Esperar a que todas las tareas se completen o sean canceladas
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                print("Verificación cancelada por el usuario")
                was_cancelled = True
                # Cancelar todas las tareas pendientes
                for task in tasks:
                    if not task.done():
                        task.cancel()
                
                # Esperar a que todas las tareas se cancelen correctamente
                await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            print(f"Error durante la verificación: {e}")
        finally:
            # Cerrar el diálogo de progreso
            progress.close()
            
            # Guardar los resultados
            self.playlist_manager.save_last_playlist()
            
            # Actualizar la interfaz
            self.update_channel_list(self.group_filter.currentText())
            
            # Contar resultados
            online_count = 0
            offline_count = 0
            slow_count = 0
            
            for channel in self.playlist_manager.channels:
                if channel.status == 'online':
                    online_count += 1
                elif channel.status == 'slow':
                    slow_count += 1
                elif channel.status == 'offline':
                    offline_count += 1
                    
            # Mostrar resultados
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
    
    def save_working_channels(self):
        """Guarda solo los canales que funcionan en un archivo M3U"""
        file_name, _ = QFileDialog.getSaveFileName(self, 'Guardar Canales Funcionales',
                                                '', 'M3U Files (*.m3u);;M3U8 Files (*.m3u8)')
        if file_name:
            self.playlist_manager.save_working_channels(file_name)
            QMessageBox.information(self, 'Canales Guardados', 
                                  f'Los canales funcionales han sido guardados en:\n{file_name}')
    
    def process_and_filter_channels_background(self):
        """Procesa y filtra canales en segundo plano"""
        file_name, _ = QFileDialog.getOpenFileName(self, 'Selecciona una lista M3U para procesar', 
                                                '', 'M3U Files (*.m3u *.m3u8)')
        if file_name:
            import threading
            thread = threading.Thread(target=self.process_and_filter_channels, args=(file_name,), daemon=True)
            thread.start()
            
            QMessageBox.information(self, 'Procesamiento Iniciado', 
                                  'El procesamiento de la lista ha comenzado en segundo plano.\n'
                                  'Se generará un archivo con los canales funcionales en la carpeta temporal del sistema.\n'
                                  'Revise la consola para ver el progreso y la ubicación del archivo resultante.')
    
    def process_and_filter_channels(self, file_path):
        """Procesa y filtra canales de una lista M3U"""
        # Procesar la lista seleccionada (no la actual), sin afectar la UI
        import asyncio
        import tempfile
        from datetime import datetime
        from src.core.playlist_manager import PlaylistManager
        
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
