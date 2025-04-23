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
                except (aiohttp.ClientError, asyncio.TimeoutError, ConnectionResetError, ssl.SSLError) as e:
                    # Manejo específico para errores de conexión
                    print(f"Error de conexión al verificar canal {channel.name}: {str(e)}")
                    channel.status = 'offline'
                    channel.response_time = None
                    channel.last_check = datetime.now().isoformat()
        except Exception as e:
            # Capturar cualquier otra excepción
            print(f"Error inesperado al verificar canal {channel.name}: {str(e)}")
            channel.status = 'offline'
            channel.response_time = None
            channel.last_check = datetime.now().isoformat()

    async def check_all_channels(self) -> None:
        # Limitar el número de conexiones simultáneas
        MAX_CONCURRENT = 50  # Ajustar según necesidad y recursos del sistema
        semaphore = asyncio.Semaphore(MAX_CONCURRENT)
        
        async def check_channel_with_semaphore(channel):
            async with semaphore:
                return await self.check_channel(channel)
        
        # Crear tareas para verificar cada canal
        tasks = []
        for channel in self.channels:
            task = asyncio.create_task(check_channel_with_semaphore(channel))
            tasks.append(task)
        
        # Procesar las tareas con manejo de errores
        completed_tasks = 0
        failed_tasks = 0
        error_types = {}
        
        try:
            for task in asyncio.as_completed(tasks):
                try:
                    await task
                    completed_tasks += 1
                except asyncio.CancelledError:
                    # Cancelar todas las tareas pendientes
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    raise  # Re-raise para que se maneje en el nivel superior
                except Exception as e:
                    # Registrar el tipo de error para análisis
                    error_type = type(e).__name__
                    if error_type not in error_types:
                        error_types[error_type] = 0
                    error_types[error_type] += 1
                    
                    print(f"Error en tarea de verificación: {e}")
                    failed_tasks += 1
        except asyncio.CancelledError:
            print("Verificación cancelada. Limpiando recursos...")
            # Asegurarse de que todas las tareas se cancelen
            for task in tasks:
                if not task.done():
                    task.cancel()
            try:
                # Esperar a que todas las tareas se cancelen (con timeout)
                await asyncio.wait(tasks, timeout=5)
            except Exception as e:
                print(f"Error durante la cancelación de tareas: {e}")
            raise
        finally:
            # Limpiar recursos
            for task in tasks:
                if not task.done():
                    task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass
        
        # Mostrar resumen de errores
        if error_types:
            print("Resumen de errores encontrados:")
            for error_type, count in error_types.items():
                print(f"  - {error_type}: {count} ocurrencias")
        
        print(f"Verificación completada: {completed_tasks} canales procesados, {failed_tasks} fallidos")
        
        # Guardar los resultados
        try:
            self.save_last_playlist()
        except Exception as e:
            print(f"Error al guardar la lista de reproducción: {e}")
            # Intentar guardar en una ubicación alternativa si falla
            try:
                backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_last_playlist.json"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'channels': [asdict(ch) for ch in self.channels],
                        'groups': self.groups
                    }, f, ensure_ascii=False, indent=2)
                print(f"Se ha creado una copia de seguridad en: {backup_path}")
            except Exception as backup_error:
                print(f"No se pudo crear copia de seguridad: {backup_error}")
    
    def save_working_channels(self, file_path: str) -> None:
        working_channels = [ch for ch in self.channels if ch.status in ['online', 'slow']]
        if working_channels:
            self.save_m3u_playlist(file_path, working_channels)
            print(f"Saved {len(working_channels)} working channels to {file_path}")
        else:
            print("No working channels found to save")

    def save_m3u_playlist(self, file_path: str, channels: Optional[List[Channel]] = None) -> None:
        if channels is None:
            channels = self.channels

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('#EXTM3U\n')
            for channel in channels:
                status_tag = f'tvg-status="{channel.status}"' if channel.status != 'unknown' else ''
                response_time_tag = f'tvg-response-time="{channel.response_time:.2f}"' if channel.response_time is not None else ''
                last_check_tag = f'tvg-last-check="{channel.last_check}"' if channel.last_check else ''
                logo_tag = f'tvg-logo="{channel.logo}"' if channel.logo else ''
                group_tag = f'group-title="{channel.group}"' if channel.group else ''

                extinf_line = f'#EXTINF:-1 tvg-name="{channel.name}" {logo_tag} {group_tag} {status_tag} {response_time_tag} {last_check_tag},{channel.name}\n'
                f.write(extinf_line)
                f.write(f'{channel.url}\n')
    
    def load_playlist(self, file_path: str, progress_callback=None) -> None:
        self.channels.clear()
        self.groups.clear()
        
        def process_lines(lines):
            current_channel = None
            line_number = 0
            total_lines = len(lines)
            processed_lines = ['#EXTM3U']
            needs_processing = False
            channel_count = 1
            
            # Procesar cada línea y completar metadatos faltantes
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Si es una línea EXTINF, mantenerla y su URL
                if line.startswith('#EXTINF'):
                    processed_lines.append(line)
                    # Buscar la siguiente línea no vacía que debería ser la URL
                    while i + 1 < len(lines):
                        i += 1
                        next_line = lines[i].strip()
                        if next_line and not next_line.startswith('#'):
                            processed_lines.append(next_line)
                            break
                        elif next_line:
                            processed_lines.append(next_line)
                # Si es una URL sin metadatos, crear los metadatos
                elif line.startswith(('http://', 'https://', 'rtsp://', 'rtmp://', 'mmsh://')):
                    needs_processing = True
                    new_extinf = f'#EXTINF:-1 tvg-name="Canal {channel_count}" group-title="Sin Grupo" tvg-status="online",Canal {channel_count}'
                    processed_lines.append(new_extinf)
                    processed_lines.append(line)
                    channel_count += 1
                else:
                    processed_lines.append(line)
                i += 1
            
            # Si se encontraron URLs sin metadatos, guardar la nueva lista procesada
            if needs_processing:
                new_file_path = os.path.join(os.path.dirname(file_path), 'processed_' + os.path.basename(file_path))
                try:
                    with open(new_file_path, 'w', encoding='utf-8') as f:
                        f.write('\n'.join(processed_lines))
                    print(f"Lista procesada guardada en: {new_file_path}")
                except Exception as e:
                    print(f"Error al guardar la lista procesada: {e}")
            
            # Procesar la lista final
            current_channel = None
            for line in processed_lines:
                line_number += 1
                if progress_callback:
                    progress_callback((line_number / len(processed_lines)) * 100, len(self.channels))
                
                try:
                    if line.startswith('#EXTINF'):
                        # Extraer nombre y metadatos del canal
                        name_match = re.search('tvg-name="([^"]*)"', line)
                        group_match = re.search('group-title="([^"]*)"', line)
                        logo_match = re.search('tvg-logo="([^"]*)"', line)
                        
                        name = name_match.group(1) if name_match else ''
                        if not name:
                            # Buscar el nombre al final de la línea
                            name = line.split(',')[-1].strip()
                            if not name:
                                name = f'Canal {len(self.channels) + 1}'
                        
                        group = group_match.group(1) if group_match else 'Sin Grupo'
                        logo = logo_match.group(1) if logo_match else None
                        
                        current_channel = Channel(name=name, url='', group=group, logo=logo)
                        
                        if group not in self.groups:
                            self.groups.append(group)
                            
                    elif line.startswith(('http://', 'https://', 'rtsp://', 'rtmp://', 'mmsh://')):
                        # Si no hay un canal actual pero hay una URL, crear un canal nuevo
                        if not current_channel:
                            name = f'Canal {len(self.channels) + 1}'
                            current_channel = Channel(name=name, url='', group='Sin Grupo')
                            if 'Sin Grupo' not in self.groups:
                                self.groups.append('Sin Grupo')
                        
                        try:
                            # Validar la URL antes de asignarla
                            parsed_url = urllib.parse.urlparse(line)
                            if not parsed_url.scheme or not parsed_url.netloc:
                                print(f"URL malformada en línea {line_number}: {line}")
                                current_channel.status = 'offline'
                            current_channel.url = line
                            self.channels.append(current_channel)
                            current_channel = None
                        except Exception as url_error:
                            print(f"Error al procesar URL en línea {line_number}: {line}")
                            print(f"Detalle del error: {str(url_error)}")
                            if current_channel:
                                current_channel.status = 'offline'
                                current_channel.url = line
                                self.channels.append(current_channel)
                                current_channel = None
                except Exception as line_error:
                    print(f"Error procesando línea {line_number}: {line}")
                    print(f"Detalle del error: {str(line_error)}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            process_lines(lines)
            
        except UnicodeDecodeError as e:
            print(f"Error de codificación al leer el archivo {file_path}: {e}")
            print("Intentando con codificación alternativa...")
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                process_lines(lines)
            except Exception as alt_error:
                print(f"Error al procesar el archivo con codificación alternativa: {str(alt_error)}")
                raise
        
        print(f"Lista cargada: {len(self.channels)} canales en {len(self.groups)} grupos")
    
    def get_channels_by_group(self, group: str) -> List[Channel]:
        if group == 'Todos los grupos':
            return self.channels
        return [channel for channel in self.channels if channel.group == group]
        
    async def download_playlist_from_url(self, url: str) -> Tuple[bool, str, str]:
        """Descarga una lista M3U desde una URL y la guarda localmente.
        
        Args:
            url: La URL de la lista M3U a descargar.
            
        Returns:
            Tuple[bool, str, str]: (éxito, mensaje, ruta_del_archivo)
        """
        try:
            print(f"Iniciando descarga desde: {url}")
            # Crear un nombre de archivo basado en la URL
            parsed_url = urllib.parse.urlparse(url)
            file_name = os.path.basename(parsed_url.path)
            
            # Si no hay nombre de archivo en la URL, usar un nombre genérico
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
        
    def remove_duplicate_channels(self) -> None:
        """
        Elimina canales duplicados basados en la URL y unifica nombres similares.
        
        Esta función:
        1. Elimina canales duplicados por URL, combinando sus atributos
        2. Unifica nombres similares de canales (ej. "Canal HD", "Canal FHD", etc.)
        3. Ordena los canales por nombre
        """
        if not self.channels:
            return
            
        # Diccionario para agrupar canales por URL
        channels_by_url = {}
        
        # Patrones comunes para normalizar nombres
        name_patterns = {
            r'(?i)\s*(HD|SD|FHD|UHD|4K|FULL HD)': '',  # Eliminar indicadores de calidad
            r'(?i)\s*\(\d+\)': '',  # Eliminar números entre paréntesis
            r'(?i)\s*\[\d+\]': '',  # Eliminar números entre corchetes
            r'(?i)\s*\+\d+': '',    # Eliminar +1, +2, etc.
            r'(?i)\s*\d+p': '',     # Eliminar resoluciones como 720p, 1080p
            r'(?i)\s*TV\b': '',     # Eliminar "TV" al final
            r'(?i)\s*TELEVISION\b': '', # Eliminar "TELEVISION"
            r'(?i)^EL\s+': '',      # Eliminar "EL" al principio
            r'(?i)^LA\s+': '',      # Eliminar "LA" al principio
            r'(?i)^LOS\s+': '',     # Eliminar "LOS" al principio
            r'(?i)^LAS\s+': '',     # Eliminar "LAS" al principio
        }
        
        # Primera pasada: agrupar por URL y normalizar nombres
        normalized_names_map = {}  # Mapeo de nombre normalizado a lista de canales
        
        for channel in self.channels:
            if not channel.url:
                continue
                
            # Normalizar el nombre
            normalized_name = channel.name
            for pattern, replacement in name_patterns.items():
                normalized_name = re.sub(pattern, replacement, normalized_name)
            normalized_name = normalized_name.strip().lower()
            
            # Agrupar por URL
            if channel.url in channels_by_url:
                channels_by_url[channel.url].append((channel, normalized_name))
            else:
                channels_by_url[channel.url] = [(channel, normalized_name)]
                
            # Agrupar por nombre normalizado
            if normalized_name:
                if normalized_name in normalized_names_map:
                    normalized_names_map[normalized_name].append(channel)
                else:
                    normalized_names_map[normalized_name] = [channel]
        
        # Segunda pasada: unificar canales duplicados por URL
        unified_channels = []
        for url, channel_list in channels_by_url.items():
            if len(channel_list) == 1:
                # No hay duplicados para esta URL
                unified_channels.append(channel_list[0][0])
            else:
                # Combinar atributos de canales duplicados
                combined_channel = self._combine_duplicate_channels(channel_list)
                unified_channels.append(combined_channel)
        
        # Tercera pasada: unificar nombres muy similares (incluso con URLs diferentes)
        # Primero, agrupar por raíz del nombre
        name_roots = {}
        for channel in unified_channels:
            # Normalizar y simplificar aún más el nombre
            simple_name = channel.name.lower()
            for pattern, replacement in name_patterns.items():
                simple_name = re.sub(pattern, replacement, simple_name)
            
            # Eliminar caracteres no alfanuméricos y espacios múltiples
            simple_name = re.sub(r'[^\w\s]', '', simple_name)
            simple_name = re.sub(r'\s+', ' ', simple_name).strip()
            
            # Obtener la raíz del nombre (primeras palabras significativas)
            name_parts = simple_name.split()
            if len(name_parts) > 0:
                # Usar las primeras 2 palabras como máximo como raíz del nombre
                root = ' '.join(name_parts[:min(2, len(name_parts))])
                
                if len(root) >= 3:  # Solo considerar raíces con al menos 3 caracteres
                    if root in name_roots:
                        name_roots[root].append(channel)
                    else:
                        name_roots[root] = [channel]
        
        # Unificar nombres de canales con la misma raíz
        for root, channels in name_roots.items():
            if len(channels) > 1:
                # Obtener el mejor nombre para este grupo
                all_names = [ch.name for ch in channels]
                best_name = self._get_best_channel_name(all_names)
                
                # Asignar el mejor nombre a todos los canales de este grupo
                for channel in channels:
                    channel.name = best_name
        
        # Ordenar canales por nombre
        unified_channels.sort(key=lambda x: x.name.lower())
        
        # Actualizar la lista de canales
        self.channels = unified_channels
        
        # Actualizar grupos
        self.groups = sorted(list(set(ch.group for ch in self.channels if ch.group)))
        if 'Sin Grupo' in self.groups:
            # Asegurar que "Sin Grupo" esté al final
            self.groups.remove('Sin Grupo')
            self.groups.append('Sin Grupo')
            
        print(f"Canales unificados: {len(self.channels)} canales en {len(self.groups)} grupos")
    
    def _combine_duplicate_channels(self, channel_list):
        """
        Combina los atributos de canales duplicados en uno solo.
        
        Args:
            channel_list: Lista de tuplas (canal, nombre_normalizado)
            
        Returns:
            Channel: Canal combinado con los mejores atributos
        """
        # Ordenar por estado (online > slow > unknown > offline)
        status_priority = {'online': 0, 'slow': 1, 'unknown': 2, 'offline': 3}
        sorted_channels = sorted(channel_list, key=lambda x: status_priority.get(x[0].status, 4))
        
        # Usar el primer canal (mejor estado) como base
        base_channel = sorted_channels[0][0]
        
        # Elegir el mejor nombre
        all_names = [ch[0].name for ch in channel_list]
        best_name = self._get_best_channel_name(all_names)
        
        # Combinar atributos
        combined = Channel(
            name=best_name,
            url=base_channel.url,
            group=base_channel.group,
            logo=next((ch[0].logo for ch in sorted_channels if ch[0].logo), None),
            status=base_channel.status,
            response_time=base_channel.response_time,
            last_check=base_channel.last_check
        )
        
        return combined
    
    def _get_best_channel_name(self, names):
        """
        Elige el mejor nombre entre varias opciones para un canal.
        
        Args:
            names: Lista de nombres de canal
            
        Returns:
            str: El nombre más representativo
        """
        if not names:
            return ""
            
        # Preferir nombres más largos que no sean excesivamente largos
        filtered_names = [name for name in names if 3 < len(name) < 30]
        if not filtered_names:
            filtered_names = names
            
        # Preferir nombres sin caracteres especiales extraños
        clean_names = [name for name in filtered_names 
                      if not re.search(r'[^\w\s\-+&()[\]áéíóúÁÉÍÓÚñÑ]', name)]
        if clean_names:
            filtered_names = clean_names
            
        # Preferir nombres sin números al final
        names_without_numbers = [name for name in filtered_names 
                                if not re.search(r'\d+$', name)]
        if names_without_numbers:
            filtered_names = names_without_numbers
            
        # Si hay varios candidatos, elegir el más corto entre ellos
        if filtered_names:
            return min(filtered_names, key=len)
        
        # Si no hay candidatos después del filtrado, devolver el primero
        return names[0]