import re
import json
import os
import tempfile
import ssl
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Literal, Tuple
import asyncio
import aiohttp
from datetime import datetime
import urllib.parse

@dataclass
class Channel:
    name: str
    url: str
    group: Optional[str] = None
    logo: Optional[str] = None
    status: Literal['unknown', 'online', 'slow', 'offline'] = 'unknown'
    response_time: Optional[float] = None
    last_check: Optional[str] = None

class PlaylistManager:
    def __init__(self):
        self.channels: List[Channel] = []
        self.groups: List[str] = []
        self.last_playlist_path: str = 'last_playlist.json'
        self.download_dir: str = os.path.join(tempfile.gettempdir(), 'tv_ip_playlists')
        os.makedirs(self.download_dir, exist_ok=True)
        self._load_last_playlist()

    def _load_last_playlist(self) -> None:
        if os.path.exists(self.last_playlist_path):
            try:
                with open(self.last_playlist_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.channels = [Channel(**ch) for ch in data['channels']]
                    self.groups = data['groups']
            except Exception as e:
                print(f"Error loading last playlist: {e}")

    def save_last_playlist(self) -> None:
        try:
            data = {
                'channels': [asdict(ch) for ch in self.channels],
                'groups': self.groups
            }
            with open(self.last_playlist_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving last playlist: {e}")

    async def check_channel(self, channel: Channel) -> None:
        try:
            start_time = datetime.now()
            # Configurar el ClientSession con opciones más robustas
            timeout = aiohttp.ClientTimeout(total=5, connect=3)
            # Configurar el conector para ignorar errores SSL y mejorar la estabilidad
            connector = aiohttp.TCPConnector(
                force_close=True, 
                limit=1, 
                enable_cleanup_closed=True,
                ssl=False  # Ignorar verificación SSL para evitar errores con certificados autofirmados
            )
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                try:
                    # Intentar primero con HEAD, que es más rápido
                    try:
                        async with session.head(channel.url, timeout=timeout) as response:
                            end_time = datetime.now()
                            response_time = (end_time - start_time).total_seconds()
                            
                            channel.response_time = response_time
                            channel.last_check = datetime.now().isoformat()
                            
                            if response.status == 200:
                                if response_time > 2.0:
                                    channel.status = 'slow'
                                else:
                                    channel.status = 'online'
                            else:
                                # Si HEAD falla, intentar con GET
                                raise aiohttp.ClientResponseError(None, None, status=response.status)
                    except (aiohttp.ClientResponseError, aiohttp.ClientError):
                        # Si HEAD falla, intentar con GET que es más compatible con algunos servidores
                        async with session.get(channel.url, timeout=timeout) as response:
                            end_time = datetime.now()
                            response_time = (end_time - start_time).total_seconds()
                            
                            channel.response_time = response_time
                            channel.last_check = datetime.now().isoformat()
                            
                            if response.status == 200:
                                if response_time > 2.0:
                                    channel.status = 'slow'
                                else:
                                    channel.status = 'online'
                            else:
                                channel.status = 'offline'
                except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                    # Manejar errores de conexión y tiempos de espera
                    channel.status = 'offline'
                    channel.response_time = None
                    channel.last_check = datetime.now().isoformat()
                    print(f"Error al verificar canal '{channel.name}': {e}")
                except Exception as e:
                    # Capturar cualquier otra excepción
                    channel.status = 'offline'
                    channel.response_time = None
                    channel.last_check = datetime.now().isoformat()
                    print(f"Error inesperado al verificar canal '{channel.name}': {e}")
        except Exception as e:
            # Capturar excepciones en la creación de la sesión
            channel.status = 'offline'
            channel.response_time = None
            channel.last_check = datetime.now().isoformat()
            print(f"Error crítico al verificar canal '{channel.name}': {e}")

    async def check_all_channels(self) -> None:
        """Verifica el estado de todos los canales de manera concurrente y eficiente."""
        if not self.channels:
            print("No hay canales para verificar")
            return
            
        # Función auxiliar para verificar un canal con semáforo
        async def check_channel_with_semaphore(channel):
            async with semaphore:
                await self.check_channel(channel)
                
        # Crear un semáforo para limitar la concurrencia
        semaphore = asyncio.Semaphore(10)  # Máximo 10 verificaciones simultáneas
        
        # Crear tareas para verificar todos los canales
        tasks = []
        for channel in self.channels:
            task = asyncio.create_task(check_channel_with_semaphore(channel))
            tasks.append(task)
            
        # Esperar a que todas las tareas se completen, con manejo de cancelación
        try:
            # Iniciar todas las tareas
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            # Si se cancela la operación, cancelar todas las tareas pendientes
            print("Operación de verificación cancelada")
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Esperar a que todas las tareas se cancelen correctamente
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Propagar la cancelación
            raise
        except Exception as e:
            # Manejar otras excepciones
            print(f"Error durante la verificación de canales: {e}")
            
            # Cancelar tareas pendientes
            for task in tasks:
                if not task.done():
                    task.cancel()
                    
            # Esperar a que todas las tareas se cancelen correctamente
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # Contar resultados
            online_count = 0
            offline_count = 0
            slow_count = 0
            
            for channel in self.channels:
                if channel.status == 'online':
                    online_count += 1
                elif channel.status == 'slow':
                    slow_count += 1
                elif channel.status == 'offline':
                    offline_count += 1
                    
            print(f"Verificación completada:")
            print(f"- Canales en línea: {online_count}")
            print(f"- Canales lentos: {slow_count}")
            print(f"- Canales fuera de línea: {offline_count}")
            print(f"- Total verificado: {len(self.channels)}")
            
            # Guardar los resultados
            self.save_last_playlist()

    def save_working_channels(self, file_path: str) -> None:
        """Guarda solo los canales que funcionan (online o slow) en un archivo M3U."""
        working_channels = [ch for ch in self.channels if ch.status in ['online', 'slow']]
        if working_channels:
            self.save_m3u_playlist(file_path, working_channels)

    def save_m3u_playlist(self, file_path: str, channels: Optional[List[Channel]] = None) -> None:
        """Guarda los canales en formato M3U."""
        if channels is None:
            channels = self.channels
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for channel in channels:
                logo_attr = f' tvg-logo="{channel.logo}"' if channel.logo else ''
                group_attr = f' group-title="{channel.group}"' if channel.group else ''
                f.write(f'#EXTINF:-1{logo_attr}{group_attr},{channel.name}\n')
                f.write(f'{channel.url}\n')

    def load_playlist(self, file_path: str, progress_callback=None) -> None:
        """Carga una lista de reproducción desde un archivo M3U."""
        def process_lines(lines):
            channels = []
            groups = set()
            
            i = 0
            total_lines = len(lines)
            current_channel = None
            
            while i < total_lines:
                line = lines[i].strip()
                i += 1
                
                # Actualizar progreso cada 10 líneas
                if i % 10 == 0 and progress_callback:
                    percent = (i / total_lines) * 100
                    progress_callback(percent, len(channels))
                
                # Ignorar líneas vacías y comentarios que no sean EXTINF
                if not line or (line.startswith('#') and not line.startswith('#EXTINF:')):
                    continue
                
                # Procesar línea EXTINF
                if line.startswith('#EXTINF:'):
                    # Extraer atributos y nombre del canal
                    attrs = {}
                    
                    # Extraer el nombre del canal (después de la última coma)
                    parts = line.split(',', 1)
                    if len(parts) < 2:
                        # Si no hay coma, no hay nombre de canal válido
                        continue
                        
                    channel_name = parts[1].strip()
                    
                    # Extraer atributos como tvg-logo y group-title
                    attr_part = parts[0]  # Parte que contiene los atributos
                    
                    # Buscar tvg-logo
                    logo_match = re.search(r'tvg-logo="([^"]*)"', attr_part)
                    logo = logo_match.group(1) if logo_match else None
                    
                    # Buscar group-title
                    group_match = re.search(r'group-title="([^"]*)"', attr_part)
                    group = group_match.group(1) if group_match else None
                    
                    if group:
                        groups.add(group)
                    
                    # Crear objeto de canal parcial (sin URL todavía)
                    current_channel = {
                        'name': channel_name,
                        'logo': logo,
                        'group': group
                    }
                    
                # Si tenemos un canal parcial y esta línea no es un comentario, es la URL
                elif current_channel is not None and not line.startswith('#'):
                    # Añadir URL al canal y agregarlo a la lista
                    current_channel['url'] = line
                    
                    # Crear objeto Channel
                    channel = Channel(
                        name=current_channel['name'],
                        url=current_channel['url'],
                        logo=current_channel['logo'],
                        group=current_channel['group']
                    )
                    
                    channels.append(channel)
                    current_channel = None
            
            return channels, list(groups)
        
        try:
            # Verificar que el archivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"El archivo {file_path} no existe")
                
            # Leer el archivo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Verificar que es un archivo M3U válido
            if not content.strip().startswith('#EXTM3U'):
                raise ValueError("El archivo no parece ser una lista M3U válida")
                
            # Procesar líneas
            lines = content.splitlines()
            
            # Iniciar progreso
            if progress_callback:
                progress_callback(0, 0)
                
            # Procesar el contenido
            channels, groups = process_lines(lines)
            
            # Actualizar el estado del gestor
            self.channels = channels
            self.groups = groups
            
            # Finalizar progreso
            if progress_callback:
                progress_callback(100, len(channels))
                
            # Guardar la lista cargada
            self.save_last_playlist()
            
            print(f"Lista cargada: {len(channels)} canales en {len(groups)} grupos")
            
        except UnicodeDecodeError:
            # Intentar con otra codificación
            try:
                with open(file_path, 'r', encoding='latin-1', errors='ignore') as f:
                    content = f.read()
                    
                # Verificar que es un archivo M3U válido
                if not content.strip().startswith('#EXTM3U'):
                    raise ValueError("El archivo no parece ser una lista M3U válida")
                    
                # Procesar líneas
                lines = content.splitlines()
                
                # Procesar el contenido
                channels, groups = process_lines(lines)
                
                # Actualizar el estado del gestor
                self.channels = channels
                self.groups = groups
                
                # Finalizar progreso
                if progress_callback:
                    progress_callback(100, len(channels))
                    
                # Guardar la lista cargada
                self.save_last_playlist()
                
                print(f"Lista cargada (codificación alternativa): {len(channels)} canales en {len(groups)} grupos")
                
            except Exception as e:
                raise ValueError(f"Error al procesar el archivo con codificación alternativa: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error al cargar la lista: {str(e)}")

    def get_channels_by_group(self, group: str) -> List[Channel]:
        """Obtiene los canales de un grupo específico o todos si group es 'Todos los grupos'."""
        if group == 'Todos los grupos':
            return self.channels
        return [ch for ch in self.channels if ch.group == group]

    async def download_playlist_from_url(self, url: str) -> Tuple[bool, str, str]:
        """
        Descarga una lista M3U desde una URL y la guarda localmente.
        
        Args:
            url: La URL de la lista M3U a descargar.
            
        Returns:
            Tuple[bool, str, str]: (éxito, mensaje, ruta_del_archivo)
        """
        try:
            # Validar URL
            if not url or not url.startswith(('http://', 'https://')):
                return False, "URL inválida. Debe comenzar con http:// o https://", ""
                
            # Extraer nombre de archivo de la URL o generar uno
            parsed_url = urllib.parse.urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            
            # Si no hay nombre de archivo en la URL, generar uno
            if not file_name or '.' not in file_name:
                file_name = f"playlist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.m3u"
            elif not file_name.endswith(('.m3u', '.m3u8')):
                file_name += '.m3u'
                
            local_path = os.path.join(self.download_dir, file_name)
            print(f"Archivo de destino: {local_path}")
            
            # Configurar el ClientSession con opciones más robustas
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            # Configurar el conector para ignorar errores SSL y mejorar la estabilidad
            connector = aiohttp.TCPConnector(
                force_close=True, 
                limit=1, 
                enable_cleanup_closed=True,
                ssl=False  # Ignorar verificación SSL para evitar errores con certificados autofirmados
            )
            
            # Descargar el archivo con manejo de errores mejorado
            try:
                async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                    try:
                        print(f"Conectando a {url}...")
                        async with session.get(url, timeout=timeout) as response:
                            if response.status != 200:
                                error_msg = f"Error al descargar: código {response.status}"
                                print(error_msg)
                                return False, error_msg, ""
                            
                            print("Descargando contenido...")
                            content = await response.text()
                            content_length = len(content)
                            print(f"Contenido descargado: {content_length} bytes")
                            
                            # Verificar que el contenido parece ser una lista M3U
                            if not content.strip().startswith('#EXTM3U'):
                                error_msg = "El archivo descargado no parece ser una lista M3U válida"
                                print(f"{error_msg}. Primeros 100 caracteres: {content[:100]}")
                                return False, error_msg, ""
                            
                            # Guardar el archivo localmente
                            try:
                                with open(local_path, 'w', encoding='utf-8') as f:
                                    f.write(content)
                                print(f"Archivo guardado correctamente en {local_path}")
                            except UnicodeEncodeError as encode_error:
                                print(f"Error de codificación al guardar: {encode_error}")
                                # Intentar con otra codificación
                                with open(local_path, 'w', encoding='latin-1') as f:
                                    f.write(content)
                                print(f"Archivo guardado con codificación alternativa en {local_path}")
                            
                            return True, f"Lista descargada correctamente: {file_name}", local_path
                    except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError) as e:
                        error_msg = f"Error de conexión durante la descarga: {str(e)}"
                        print(error_msg)
                        return False, error_msg, ""
            except Exception as e:
                error_msg = f"Error en la sesión HTTP: {str(e)}"
                print(error_msg)
                return False, error_msg, ""
                    
        except Exception as e:
            error_msg = f"Error inesperado al descargar la lista: {str(e)}"
            print(error_msg)
            return False, error_msg, ""
            
    def download_playlist_from_url_sync(self, url: str) -> Tuple[bool, str, str]:
        """Versión sincrónica del método download_playlist_from_url."""
        return asyncio.run(self.download_playlist_from_url(url))
