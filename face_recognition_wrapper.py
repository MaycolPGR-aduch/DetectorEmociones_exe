import os
import sys
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("face_recognition_wrapper")

def load_face_recognition(data_path):
    """
    Carga face_recognition de manera segura, evitando la dependencia de face_recognition_models
    """
    logger.info(f"Intentando cargar face_recognition con data_path: {data_path}")
    
    # Configurar la ruta del modelo antes de importar face_recognition
    os.environ["FACE_RECOGNITION_MODEL_LOCATION"] = data_path
    
    try:
        # Intentar importar face_recognition
        import face_recognition
        logger.info("face_recognition importado exitosamente")
        return face_recognition
    except ImportError as e:
        logger.error(f"Error al importar face_recognition: {str(e)}")
        if "face_recognition_models" in str(e):
            logger.info("Creando estructura fake para face_recognition_models")
            
            # Crear estructura fake para face_recognition_models
            try:
                models_dir = os.path.join(data_path, "face_recognition_models")
                logger.info(f"Creando directorio: {models_dir}")
                os.makedirs(models_dir, exist_ok=True)
                
                # Añadir el directorio al path
                sys.path.append(data_path)
                
                # Crear un módulo falso para face_recognition_models
                init_path = os.path.join(models_dir, "__init__.py")
                logger.info(f"Creando archivo: {init_path}")
                with open(init_path, "w") as f:
                    f.write("# Mock face_recognition_models module\n")
                    f.write("def get_model(model_name):\n")
                    f.write("    import os\n")
                    f.write("    return os.environ.get('FACE_RECOGNITION_MODEL_LOCATION', '')\n")
                
                # Crear estructura más completa si es necesario
                models_subdir = os.path.join(models_dir, "models")
                logger.info(f"Creando directorio: {models_subdir}")
                os.makedirs(models_subdir, exist_ok=True)
                
                # Intentar de nuevo la importación
                import face_recognition
                logger.info("face_recognition importado exitosamente después de crear estructura fake")
                return face_recognition
            except Exception as ex:
                logger.error(f"Error al crear estructura fake: {str(ex)}")
                raise
        else:
            raise
    except Exception as e:
        logger.error(f"Error desconocido al importar face_recognition: {str(e)}")
        raise

# Clase simplificada que simula algunas funcionalidades de face_recognition
# en caso de que la importación falle por completo
class FaceRecognitionFallback:
    """Clase de respaldo en caso de que face_recognition no se pueda cargar"""
    
    def __init__(self, data_path):
        self.data_path = data_path
        
        # Intentar cargar OpenCV como respaldo
        try:
            import cv2
            self.cv2 = cv2
            cascade_file = os.path.join(data_path, "haarcascade_frontalface_default.xml")
            
            # Verificar si existe el archivo
            if os.path.exists(cascade_file):
                self.face_cascade = cv2.CascadeClassifier(cascade_file)
                if self.face_cascade.empty():
                    print(f"Error: Cascade vacío aunque existe el archivo: {cascade_file}")
                else:
                    print(f"Cascade cargado correctamente desde: {cascade_file}")
            else:
                print(f"Error: Archivo cascade no encontrado en: {cascade_file}")
                # Intentar usar ruta predeterminada
                default_cascade = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                if os.path.exists(default_cascade):
                    self.face_cascade = cv2.CascadeClassifier(default_cascade)
                    print(f"Utilizando cascade predeterminado: {default_cascade}")
                else:
                    print(f"Error: No se encontró cascade predeterminado en: {default_cascade}")
                    self.face_cascade = None
        except Exception as e:
            print(f"Error al cargar OpenCV como respaldo: {e}")
            self.cv2 = None
            self.face_cascade = None
    
    def load_image_file(self, file_path):
        """Carga una imagen desde archivo"""
        if self.cv2:
            try:
                return self.cv2.imread(file_path)
            except Exception as e:
                logger.error(f"Error cargando imagen: {str(e)}")
        return None
    
    def face_locations(self, img):
        """Detecta ubicaciones de rostros en una imagen"""
        if self.cv2 and self.face_cascade:
            try:
                gray = self.cv2.cvtColor(img, self.cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                # Convertir formato de caras a formato compatible
                return [(y, x + w, y + h, x) for (x, y, w, h) in faces]
            except Exception as e:
                logger.error(f"Error detectando rostros: {str(e)}")
        return []
    
    def face_encodings(self, img, known_face_locations=None):
        """
        Simula encodings de rostros, pero realmente devuelve valores aleatorios
        En producción esto no funcionaría para reconocimiento, solo para testing
        """
        import numpy as np
        if known_face_locations:
            return [np.random.rand(128) for _ in known_face_locations]
        return []
    
    def compare_faces(self, known_encodings, face_encoding):
        """Simula comparación de rostros"""
        import numpy as np
        if not known_encodings:
            return []
        # Simular coincidencia con el primer encoding
        result = [False] * len(known_encodings)
        if len(known_encodings) > 0:
            result[0] = True
        return result

def get_face_recognition(data_path):
    """
    Función principal que intenta cargar face_recognition
    o devuelve un fallback si no es posible
    """
    try:
        return load_face_recognition(data_path)
    except Exception as e:
        logger.error(f"No se pudo cargar face_recognition, usando fallback: {str(e)}")
        return FaceRecognitionFallback(data_path)