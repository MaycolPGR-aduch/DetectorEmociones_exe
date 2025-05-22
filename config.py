import os
import sys
import cv2

def get_data_dir():
    """Encuentra la carpeta de datos tanto en desarrollo como en el ejecutable"""
    if getattr(sys, 'frozen', False):
        # Ejecutable
        base_dir = os.path.dirname(sys.executable)
        
        # Buscar en varias ubicaciones posibles
        candidates = [
            os.path.join(base_dir, 'data'),
            os.path.join(base_dir, '_internal', 'data')
        ]
        
        for candidate in candidates:
            if os.path.exists(candidate):
                print(f"Utilizando carpeta data: {candidate}")
                return candidate
                
        # Si no encontramos data, usamos la predeterminada y la creamos
        default_dir = os.path.join(base_dir, 'data')
        os.makedirs(default_dir, exist_ok=True)
        print(f"Carpeta data no encontrada, creando en: {default_dir}")
        return default_dir
    else:
        # Desarrollo
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, 'data')
        print(f"Modo desarrollo: usando carpeta data en {data_dir}")
        return data_dir

def get_cascade_file():
    """Encuentra el archivo haarcascade en varias ubicaciones posibles"""
    data_dir = get_data_dir()
    
    # Buscar primero en nuestra carpeta data
    custom_path = os.path.join(data_dir, "haarcascade_frontalface_default.xml")
    if os.path.exists(custom_path):
        print(f"Usando haarcascade personalizado: {custom_path}")
        return custom_path
        
    # Intentar con la ubicación de OpenCV
    try:
        opencv_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if os.path.exists(opencv_path):
            print(f"Usando haarcascade de OpenCV: {opencv_path}")
            return opencv_path
    except:
        pass
        
    # Última opción: buscar en el directorio actual y subcarpetas
    for root, dirs, files in os.walk('.'):
        if "haarcascade_frontalface_default.xml" in files:
            path = os.path.join(root, "haarcascade_frontalface_default.xml")
            print(f"Encontrado haarcascade en búsqueda: {path}")
            return path
            
    print("ERROR: No se pudo encontrar haarcascade_frontalface_default.xml")
    return None

# Variables globales para usar en otros módulos
DATA_DIR = get_data_dir()
CASCADE_FILE = get_cascade_file()