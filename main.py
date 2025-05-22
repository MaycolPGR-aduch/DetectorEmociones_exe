#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sistema de Detección de Emociones - Aplicación principal
"""

import os
import sys
import logging
import tkinter as tk
from tkinter import messagebox
import traceback
import shutil

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main")

def main():
    # Usar config.py para las rutas
    from config import DATA_DIR, CASCADE_FILE
    
    # Ya no necesitas determinar las rutas aquí
    logger.info(f"Usando directorio de datos: {DATA_DIR}")
    logger.info(f"Usando archivo cascade: {CASCADE_FILE}")
    
    # Verificar existencia del directorio de datos
    if not os.path.exists(DATA_DIR):
        logger.warning(f"Directorio de datos no encontrado en {DATA_DIR}, se creará")
        os.makedirs(DATA_DIR, exist_ok=True)
    
    # Verificar archivos esenciales
    for subdir in ['img', 'usuarios']:
        subpath = os.path.join(DATA_DIR, subdir)
        if not os.path.exists(subpath):
            os.makedirs(subpath, exist_ok=True)
            logger.info(f"Creado directorio: {subpath}")
    
    # Exportar las rutas como variables de entorno para compatibilidad
    os.environ["DETECTOR_DATA_PATH"] = DATA_DIR
    
    # Importar el módulo de interfaz
    try:
        from interfaz import EmotionDashboard
        
        # Iniciar la aplicación
        root = tk.Tk()
        app = EmotionDashboard(root)
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {str(e)}")
        logger.error(traceback.format_exc())
        messagebox.showerror(
            "Error", 
            f"Error al iniciar la aplicación:\n{str(e)}\n\n"
            "Revise el archivo de log para más detalles."
        )

if __name__ == "__main__":
    try:
        # Intentar configurar TensorFlow y face_recognition de manera segura
        try:
            from tensorflow_minimal import setup_minimal_tensorflow
            tf_available = setup_minimal_tensorflow()
            logger.info(f"TensorFlow disponible: {tf_available}")
        except Exception as e:
            logger.warning(f"No se pudo inicializar TensorFlow: {str(e)}")
        
        try:
            from face_recognition_wrapper import get_face_recognition
            logger.info("Face recognition wrapper cargado correctamente")
        except Exception as e:
            logger.warning(f"No se pudo cargar face_recognition_wrapper: {str(e)}")
        
        # Iniciar aplicación
        main()
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Mostrar error en UI si es posible
        try:
            messagebox.showerror(
                "Error Crítico", 
                f"La aplicación no puede iniciarse debido a un error:\n{str(e)}\n\n"
                "Revise el archivo detector_app.log para más detalles."
            )
        except:
            print(f"ERROR CRÍTICO: {str(e)}")
            print("Revise el archivo detector_app.log para más detalles.")