import os
import sys
import logging
import random

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tensorflow_minimal")

def setup_minimal_tensorflow():
    """
    Configura un entorno mínimo para usar TensorFlow o proporciona alternativas
    en caso de que TensorFlow no esté disponible o tenga problemas de DLL
    """
    # Configurar variables de entorno para reducir warnings y errores de TF
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Desactivar logs de TF
    
    # Intentar cargar TensorFlow con manejo de errores
    try:
        logger.info("Intentando cargar TensorFlow...")
        import tensorflow as tf
        tf.get_logger().setLevel('ERROR')  # Reducir logs de TF
        logger.info(f"TensorFlow cargado correctamente, versión: {tf.__version__}")
        return True
    except ImportError:
        logger.warning("No se pudo importar TensorFlow")
        return False
    except Exception as e:
        # Si hay un error de DLL, es posible que sea un problema común de GPU
        if "DLL" in str(e):
            logger.warning("Error de DLL al cargar TensorFlow, intentando forzar CPU")
            # Forzar CPU antes de reintentar
            os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
            try:
                import tensorflow as tf
                tf.get_logger().setLevel('ERROR')
                logger.info(f"TensorFlow (CPU) cargado correctamente: {tf.__version__}")
                return True
            except Exception as e2:
                logger.error(f"Error al cargar TensorFlow incluso en modo CPU: {str(e2)}")
                return False
        else:
            logger.error(f"Error desconocido al cargar TensorFlow: {str(e)}")
            return False

class TensorFlowFallback:
    """
    Clase fallback para proporcionar funcionalidades básicas similares a TensorFlow
    cuando TensorFlow no está disponible o tiene problemas
    """
    @staticmethod
    def load_model_fallback():
        """
        Proporciona un modelo 'dummy' que devuelve valores dinámicos
        para pruebas y desarrollo cuando TensorFlow no esté disponible
        """
        import numpy as np
        
        class DummyModel:
            def __init__(self):
                self.emotion_history = {}
            
            def predict(self, x):
                """Simula una predicción con valores aleatorios más dinámicos"""
                import random
                
                batch_size = x.shape[0] if hasattr(x, 'shape') and len(x.shape) > 0 else 1
                results = []
                
                for i in range(batch_size):
                    # Elegir una emoción dominante aleatoria con mayor probabilidad
                    primary_emotion = random.choice([
                        "angry", "angry", "disgust",
                        "fear", "happy", "happy", "happy",
                        "sad", "sad", "surprise", 
                        "neutral", "neutral"
                    ])
                    
                    # Generar valores base
                    emociones = {
                        "angry": random.uniform(0.05, 0.15),
                        "disgust": random.uniform(0.05, 0.15),
                        "fear": random.uniform(0.05, 0.15),
                        "happy": random.uniform(0.05, 0.15),
                        "sad": random.uniform(0.05, 0.15),
                        "surprise": random.uniform(0.05, 0.15),
                        "neutral": random.uniform(0.05, 0.15)
                    }
                    
                    # Aumentar la emoción dominante
                    emociones[primary_emotion] = random.uniform(0.4, 0.7)
                    
                    # Normalizar para que sumen 1
                    total = sum(emociones.values())
                    for k in emociones:
                        emociones[k] /= total
                    
                    results.append(emociones)
                
                return np.array(results)
                
            def __call__(self, x):
                """Permite llamar al modelo directamente"""
                return self.predict(x)
        
        return DummyModel()

def get_fer_detector():
    """
    Intenta cargar el detector FER o proporciona una alternativa
    si no está disponible
    """
    tf_available = setup_minimal_tensorflow()
    
    if tf_available:
        try:
            logger.info("Intentando cargar el detector FER...")
            from fer import FER
            
            # Buscar el modelo en múltiples ubicaciones posibles
            possible_model_paths = [
                os.path.join(os.path.dirname(__file__), "emotion_model.hdf5"),
                os.path.join(os.path.dirname(__file__), "data", "emotion_model.hdf5"),
                os.path.join(os.path.dirname(__file__), "..", "data", "emotion_model.hdf5"),
                os.path.join(os.path.dirname(__file__), "..", "fer", "data", "emotion_model.hdf5")
            ]
            
            for model_path in possible_model_paths:
                if os.path.exists(model_path):
                    logger.info(f"Encontrado modelo FER en: {model_path}")
                    try:
                        detector = FER(mtcnn=False, model_path=model_path)
                        #detector = FER(mtcnn=False, emotion_model=model_path)
                        logger.info("Detector FER cargado correctamente con modelo personalizado")
                        return detector
                    except Exception as e:
                        logger.error(f"Error al cargar FER con modelo encontrado: {str(e)}")
            
            # Si no encontramos un modelo personalizado, intentar con el predeterminado
            detector = FER(mtcnn=False)
            logger.info("Detector FER cargado correctamente")
            return detector
        except Exception as e:
            logger.error(f"Error al cargar detector FER: {str(e)}")
    else:
        logger.warning("TensorFlow no disponible, usando detector fallback")
    
    # Si no se puede cargar FER, usar un detector fallback
    class FERFallback:
        def __init__(self):
            self.face_cascade = None
            self.prev_emotions = {}  # Para mantener cierta consistencia entre frames
            self.frame_count = 0  # Contador para cambiar emociones periódicamente
            self.emotion_shift_interval = 15  # Cada cuántos frames cambiar la emoción dominante
            
            try:
                import cv2
                from config import CASCADE_FILE
                
                # Intentar cargar desde CASCADE_FILE primero
                if CASCADE_FILE and os.path.exists(CASCADE_FILE):
                    self.face_cascade = cv2.CascadeClassifier(CASCADE_FILE)
                    logger.info(f"Detector fallback inicializado con cascade personalizado: {CASCADE_FILE}")
                else:
                    # Intentar con la ruta predeterminada
                    self.face_cascade = cv2.CascadeClassifier(
                        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                    )
                    logger.info("Detector fallback inicializado con cascade de OpenCV")
            except Exception as e:
                logger.error(f"Error al inicializar detector fallback: {str(e)}")
        
        def detect_emotions(self, frame):
            """Detecta caras y asigna emociones aleatorias que varían con el tiempo"""
            try:
                import cv2
                import numpy as np
                import random
                
                if self.face_cascade is None:
                    from config import CASCADE_FILE
                    if CASCADE_FILE and os.path.exists(CASCADE_FILE):
                        self.face_cascade = cv2.CascadeClassifier(CASCADE_FILE)
                    else:
                        self.face_cascade = cv2.CascadeClassifier(
                            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                        )
                
                self.frame_count += 1
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                result = []
                
                # Actualizar si es momento de cambiar emociones o si cambió el número de caras
                should_update = (self.frame_count % self.emotion_shift_interval == 0) or (len(faces) != len(self.prev_emotions))
                
                for i, (x, y, w, h) in enumerate(faces):
                    face_id = f"face_{i}"
                    
                    if should_update or face_id not in self.prev_emotions:
                        # Elegir una emoción dominante diferente a la anterior si es posible
                        if face_id in self.prev_emotions:
                            prev_dominant = max(self.prev_emotions[face_id].items(), key=lambda x: x[1])[0]
                            other_emotions = [e for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"] if e != prev_dominant]
                            # 75% de probabilidad de cambiar a otra emoción
                            if random.random() < 0.75:
                                primary_emotion = random.choice(other_emotions)
                            else:
                                primary_emotion = prev_dominant
                        else:
                            # Primera emoción - elegir aleatoriamente
                            primary_emotion = random.choice(["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"])
                        
                        # Generar todas las emociones con valores base aleatorios
                        emociones = {
                            "angry": random.uniform(0.05, 0.15),
                            "disgust": random.uniform(0.05, 0.15),
                            "fear": random.uniform(0.05, 0.15),
                            "happy": random.uniform(0.05, 0.15),
                            "sad": random.uniform(0.05, 0.15),
                            "surprise": random.uniform(0.05, 0.15),
                            "neutral": random.uniform(0.05, 0.15)
                        }
                        
                        # Dar mayor peso a la emoción dominante
                        emociones[primary_emotion] = random.uniform(0.4, 0.7)
                        
                        # Normalizar para que sumen 1
                        suma = sum(emociones.values())
                        for k in emociones:
                            emociones[k] /= suma
                        
                        # Guardar para el próximo frame
                        self.prev_emotions[face_id] = emociones
                    else:
                        # Usar emociones previas con pequeñas variaciones para suavidad
                        emociones = {}
                        for emo, val in self.prev_emotions[face_id].items():
                            # Añadir pequeña variación aleatoria (±10%)
                            variation = random.uniform(-0.1, 0.1) * val
                            emociones[emo] = max(0.01, min(0.99, val + variation))
                        
                        # Normalizar para que sumen 1
                        suma = sum(emociones.values())
                        for k in emociones:
                            emociones[k] /= suma
                        
                        # Actualizar para el próximo frame
                        self.prev_emotions[face_id] = emociones
                    
                    result.append({"box": (x, y, w, h), "emotions": emociones})
                
                # Limpiar caras que ya no están presentes
                if len(faces) > 0:
                    current_face_ids = [f"face_{i}" for i in range(len(faces))]
                    self.prev_emotions = {k: v for k, v in self.prev_emotions.items() if k in current_face_ids}
                
                return result
            except Exception as e:
                logger.error(f"Error en detect_emotions fallback: {str(e)}")
                return []
    
    return FERFallback()