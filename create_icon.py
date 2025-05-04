#!/usr/bin/env python3
"""
Script para crear un icono para la aplicación TV IP Player
"""

from PIL import Image
import cairosvg
import io
import os

# Colores del tema
ACCENT_COLOR = "#FF8000"  # Naranja
DARK_BG = "#1E1E1E"       # Fondo oscuro

def svg_to_ico(svg_path, ico_path, sizes=[16, 32, 48, 64, 128, 256]):
    """Convierte un archivo SVG a ICO con múltiples tamaños"""
    if not os.path.exists(svg_path):
        print(f"El archivo SVG no existe: {svg_path}")
        return False
    
    # Si no tenemos un SVG real, crear uno básico
    if os.path.getsize(svg_path) < 100:
        print("El archivo SVG descargado no es válido, creando uno básico...")
        create_basic_icon(ico_path, sizes)
        return True
    
    try:
        # Convertir SVG a PNG en memoria para cada tamaño
        images = []
        for size in sizes:
            png_data = cairosvg.svg2png(url=svg_path, output_width=size, output_height=size)
            img = Image.open(io.BytesIO(png_data))
            images.append(img)
        
        # Guardar como ICO
        images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"Icono creado exitosamente: {ico_path}")
        return True
    except Exception as e:
        print(f"Error al convertir SVG a ICO: {e}")
        # Si falla, crear un icono básico
        create_basic_icon(ico_path, sizes)
        return True

def create_basic_icon(ico_path, sizes=[16, 32, 48, 64, 128, 256]):
    """Crea un icono básico con las iniciales 'TV' en el color del tema"""
    try:
        images = []
        for size in sizes:
            # Crear una imagen con fondo naranja
            img = Image.new('RGBA', (size, size), ACCENT_COLOR)
            
            # Guardar la imagen
            images.append(img)
        
        # Guardar como ICO
        images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"Icono básico creado exitosamente: {ico_path}")
        return True
    except Exception as e:
        print(f"Error al crear icono básico: {e}")
        return False

if __name__ == "__main__":
    # Rutas de archivos
    script_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(script_dir, "icon.ico")  # Usamos el archivo descargado
    ico_path = os.path.join(script_dir, "icon.ico")  # Sobrescribimos con el ICO
    
    # Crear un icono básico directamente
    create_basic_icon(ico_path)
    print(f"Icono creado en: {ico_path}")
