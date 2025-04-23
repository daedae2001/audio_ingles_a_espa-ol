import json
import os
from playlist_manager import PlaylistManager, Channel

def test_unify_channels():
    """
    Prueba la funcionalidad de unificación de canales.
    Crea una lista de canales con duplicados y nombres similares,
    y luego aplica la función remove_duplicate_channels.
    """
    # Crear una instancia de PlaylistManager
    manager = PlaylistManager()
    
    # Crear canales de prueba con URLs duplicadas y nombres similares
    channels = [
        Channel(name="Canal 1", url="http://example.com/stream1", group="Grupo 1"),
        Channel(name="Canal 1 HD", url="http://example.com/stream1", group="Grupo 1"),  # Duplicado con nombre similar
        Channel(name="Canal 2", url="http://example.com/stream2", group="Grupo 2"),
        Channel(name="Canal 2 FHD", url="http://example.com/stream2", group="Grupo 2"),  # Duplicado con nombre similar
        Channel(name="Canal 3", url="http://example.com/stream3", group="Grupo 1"),
        Channel(name="Canal 4", url="http://example.com/stream4", group="Grupo 2"),
        Channel(name="Canal 5", url="http://example.com/stream5", group="Grupo 3"),
        Channel(name="Canal 5 (1)", url="http://example.com/stream5", group="Grupo 3"),  # Duplicado con nombre similar
        Channel(name="Repetir TV", url="http://example.com/repetir1", group="Grupo 1"),
        Channel(name="Repetir HD", url="http://example.com/repetir2", group="Grupo 1"),  # Nombre similar pero URL diferente
        Channel(name="REPETIR", url="http://example.com/repetir3", group="Grupo 1"),  # Nombre similar pero URL diferente
    ]
    
    # Asignar los canales al manager
    manager.channels = channels
    manager.groups = ["Grupo 1", "Grupo 2", "Grupo 3"]
    
    # Imprimir canales originales
    print("Canales originales:")
    for i, channel in enumerate(manager.channels):
        print(f"{i+1}. {channel.name} - {channel.url} - {channel.group}")
    
    # Aplicar la función de unificación
    print("\nAplicando unificación de canales...")
    manager.remove_duplicate_channels()
    
    # Imprimir canales unificados
    print("\nCanales después de unificar:")
    for i, channel in enumerate(manager.channels):
        print(f"{i+1}. {channel.name} - {channel.url} - {channel.group}")
    
    # Verificar resultados
    print("\nResumen:")
    print(f"Canales originales: {len(channels)}")
    print(f"Canales después de unificar: {len(manager.channels)}")
    print(f"Canales eliminados: {len(channels) - len(manager.channels)}")
    
    # Verificar que los canales estén ordenados por nombre
    names = [ch.name for ch in manager.channels]
    sorted_names = sorted(names, key=lambda x: x.lower())
    is_sorted = names == sorted_names
    print(f"¿Canales ordenados por nombre? {'Sí' if is_sorted else 'No'}")
    
    # Verificar que no haya URLs duplicadas
    urls = [ch.url for ch in manager.channels]
    unique_urls = set(urls)
    no_duplicates = len(urls) == len(unique_urls)
    print(f"¿Sin URLs duplicadas? {'Sí' if no_duplicates else 'No'}")
    
    return manager

if __name__ == "__main__":
    test_unify_channels()
