"""
Script de prueba para reproducir video con VLC
"""
import os
import sys
import subprocess

def main():
    # URL de prueba (Big Buck Bunny)
    url = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    
    print(f"Intentando reproducir: {url}")
    
    # Método 1: Usar subprocess con VLC directamente
    try:
        print("\nMétodo 1: Usando subprocess con VLC directamente")
        vlc_path = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
        if os.path.exists(vlc_path):
            print(f"VLC encontrado en: {vlc_path}")
            cmd = f'"{vlc_path}" "{url}"'
            print(f"Ejecutando: {cmd}")
            subprocess.Popen(cmd, shell=True)
            input("Presiona Enter para continuar con el siguiente método...")
        else:
            print(f"VLC no encontrado en: {vlc_path}")
    except Exception as e:
        print(f"Error en Método 1: {e}")
    
    # Método 2: Usar os.startfile
    try:
        print("\nMétodo 2: Usando os.startfile")
        print(f"Abriendo URL con programa predeterminado: {url}")
        os.startfile(url)
        input("Presiona Enter para continuar con el siguiente método...")
    except Exception as e:
        print(f"Error en Método 2: {e}")
    
    # Método 3: Usar comando start
    try:
        print("\nMétodo 3: Usando comando start")
        cmd = f'start "" "{url}"'
        print(f"Ejecutando: {cmd}")
        subprocess.Popen(cmd, shell=True)
        input("Presiona Enter para continuar con el siguiente método...")
    except Exception as e:
        print(f"Error en Método 3: {e}")
    
    # Método 4: Usar python-vlc
    try:
        print("\nMétodo 4: Usando python-vlc")
        import vlc
        
        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(url)
        player.set_media(media)
        player.play()
        
        print("Reproduciendo con python-vlc. Espera 30 segundos...")
        import time
        time.sleep(30)  # Esperar 30 segundos para que se reproduzca
    except Exception as e:
        print(f"Error en Método 4: {e}")
    
    print("\nPrueba completada. ¿Funcionó alguno de los métodos?")

if __name__ == "__main__":
    main()
