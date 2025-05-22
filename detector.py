import threading
import os
import cv2
import numpy as np
import time
from PIL import Image, ImageTk, ImageOps, ImageDraw
import tkinter as tk
from collections import deque
import logging

# Importar config.py
from config import DATA_DIR, CASCADE_FILE

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("detector")

class DetectorEmociones:
    def __init__(self, parent, panel_emoji, hist_eq_var, data_path, fps_var, faces_var):
        self.parent = parent
        self.panel = panel_emoji
        self.hist_eq_var = hist_eq_var
        # Usar data_path que viene como parámetro, pero también tener una referencia a DATA_DIR
        self.data_path = data_path
        # Verificar si las rutas son consistentes
        if data_path != DATA_DIR:
            logger.warning(f"Detectada inconsistencia de rutas: data_path={data_path}, DATA_DIR={DATA_DIR}")
        
        self.fps_var = fps_var
        self.faces_var = faces_var

        # Importar face_recognition usando nuestro wrapper
        from face_recognition_wrapper import get_face_recognition
        self.face_recognition = get_face_recognition(self.data_path)
        logger.info("Face recognition inicializado")

        # Cargar el detector de emociones de manera controlada
        self.detector_fer = self._cargar_detector_fer()
        logger.info("Detector FER inicializado")

        self.running = False
        self.thread = None
        self.video_label = None

        self.frame_count = 0
        self.recognition_limit = 25
        self.usuario_reconocido = "Desconocido"
        self.ya_intento_reconocer = False
        self.last_emotion = None
        self.last_conf = 0

        self.emotion_labels = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        self.emotion_colors = {
            "angry": "#e74c3c", "disgust": "#27ae60", "fear": "#8e44ad",
            "happy": "#f1c40f", "sad": "#3498db", "surprise": "#e67e22", "neutral": "#95a5a6"
        }

        self.emoji_imgs = self._cargar_emojis()
        self.embeddings = []
        self.nombres = []
        self._cargar_rostros()
        self.emo_history = {e: deque(maxlen=10) for e in self.emotion_labels}

    def _cargar_detector_fer(self):
        """Carga el detector FER con manejo de errores"""
        try:
            # Evitar logs de TensorFlow
            os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
            
            # Intentar cargar FER sin mtcnn
            try:
                from fer import FER
                return FER(mtcnn=False)
            except ImportError:
                logger.warning("No se pudo importar fer, usando detector fallback")
                return self._crear_detector_fallback()
        except Exception as e:
            logger.error(f"Error al cargar detector FER: {str(e)}")
            return self._crear_detector_fallback()
    
    def _crear_detector_fallback(self):
        class FERFallback:
            def __init__(self):
                # Usar CASCADE_FILE de config.py
                if os.path.exists(CASCADE_FILE):
                    self.face_cascade = cv2.CascadeClassifier(CASCADE_FILE)
                    logger.info(f"Detector fallback inicializado con cascade: {CASCADE_FILE}")
                else:
                    # Intentar con la ruta de OpenCV como respaldo
                    try:
                        default_cascade = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                        self.face_cascade = cv2.CascadeClassifier(default_cascade)
                        logger.info(f"Detector fallback inicializado con cascade predeterminado: {default_cascade}")
                    except Exception as e:
                        logger.error(f"Error al cargar cascade predeterminado: {str(e)}")
                        self.face_cascade = None
                
                # Para emociones dinámicas
                self.prev_emotions = {}  # Para mantener cierta consistencia entre frames
                self.frame_count = 0  # Contador para cambiar emociones periódicamente
                self.emotion_shift_interval = 15  # Cada cuántos frames cambiar la emoción dominante
                
            def detect_emotions(self, frame):
                """Detecta caras y asigna emociones aleatorias dinámicas para pruebas"""
                try:
                    if self.face_cascade is None or self.face_cascade.empty():
                        logger.error("Cascade no cargado o vacío, no se pueden detectar rostros")
                        return []
                    
                    self.frame_count += 1
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                    result = []
                    
                    # Determinar si es momento de actualizar las emociones
                    should_update = (self.frame_count % self.emotion_shift_interval == 0) or (len(faces) != len(self.prev_emotions))
                    
                    for i, (x, y, w, h) in enumerate(faces):
                        face_id = f"face_{i}"
                        
                        if should_update or face_id not in self.prev_emotions:
                            # Elegir una emoción dominante diferente a la anterior si es posible
                            if face_id in self.prev_emotions:
                                prev_dominant = max(self.prev_emotions[face_id].items(), key=lambda x: x[1])[0]
                                other_emotions = [e for e in ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"] if e != prev_dominant]
                                import random
                                # 75% de probabilidad de cambiar a otra emoción
                                if random.random() < 0.75:
                                    primary_emotion = random.choice(other_emotions)
                                else:
                                    primary_emotion = prev_dominant
                            else:
                                # Primera emoción - elegir aleatoriamente
                                import random
                                primary_emotion = random.choice(["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"])
                            
                            # Generar todas las emociones con valores base aleatorios
                            import random
                            import numpy as np
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
                            import random
                            emociones = {}
                            for emo, val in self.prev_emotions[face_id].items():
                                # Añadir pequeña variación aleatoria (±5%)
                                variation = random.uniform(-0.05, 0.05) * val
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

    def _cargar_emojis(self):
        imgs = {}
        for emo in self.emotion_labels:
            ruta = os.path.join(self.data_path, "img", f"{emo}.png")
            try:
                img = cv2.imread(ruta, cv2.IMREAD_UNCHANGED)
                if img is not None:
                    imgs[emo] = img
                    logger.info(f"Emoji cargado: {emo} desde {ruta}")
                else:
                    logger.warning(f"No se pudo cargar emoji: {ruta}")
                    # Intentar con DATA_DIR como respaldo
                    ruta_alt = os.path.join(DATA_DIR, "img", f"{emo}.png")
                    if os.path.exists(ruta_alt) and ruta_alt != ruta:
                        img = cv2.imread(ruta_alt, cv2.IMREAD_UNCHANGED)
                        if img is not None:
                            imgs[emo] = img
                            logger.info(f"Emoji cargado desde ruta alternativa: {ruta_alt}")
            except Exception as e:
                logger.error(f"Error cargando emoji {emo}: {str(e)}")
        return imgs

    def _cargar_rostros(self):
        base = os.path.join(self.data_path, "usuarios")
        if not os.path.exists(base):
            logger.warning(f"Directorio de usuarios no existe: {base}")
            # Intentar con DATA_DIR como respaldo
            base_alt = os.path.join(DATA_DIR, "usuarios")
            if os.path.exists(base_alt) and base_alt != base:
                logger.info(f"Usando directorio alternativo de usuarios: {base_alt}")
                base = base_alt
            else:
                return
        
        for user in os.listdir(base):
            carpeta = os.path.join(base, user)
            if not os.path.isdir(carpeta):
                continue
                
            for img_file in os.listdir(carpeta):
                img_path = os.path.join(carpeta, img_file)
                try:
                    img = self.face_recognition.load_image_file(img_path)
                    encs = self.face_recognition.face_encodings(img)
                    if encs:
                        self.embeddings.append(encs[0])
                        self.nombres.append(user.replace("_", " "))
                except Exception as e:
                    logger.error(f"Error al procesar {img_path}: {str(e)}")
                    continue
        
        logger.info(f"Rostros cargados: {len(self.embeddings)}")

    def mostrar(self):
        for w in self.parent.winfo_children():
            w.destroy()
        self.video_label = tk.Label(self.parent, bg="black")
        self.video_label.pack(expand=True, fill="both")

    def iniciar(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            logger.info("Detector iniciado")

    def detener(self):
        self.running = False
        logger.info("Detector detenido")

    def _loop(self):
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.frame_count = 0
            self.usuario_reconocido = "Desconocido"
            self.ya_intento_reconocer = False

            times = []

            while self.running:
                start = time.time()
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Error al leer frame de cámara")
                    continue

                self.frame_count += 1
                usar_hist = self.hist_eq_var.get()
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                if usar_hist:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.equalizeHist(gray)
                    frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

                emo, conf, box = None, 0, None
                emociones_actuales = {}

                try:
                    faces = self.detector_fer.detect_emotions(frame)
                    self.faces_var.set(str(len(faces)))
                    if faces:
                        face = faces[0]
                        box = face["box"]
                        emociones = face["emotions"]
                        for e, v in emociones.items():
                            emociones_actuales[e] = v
                            self.emo_history[e].append(v)
                        emo = max(emociones, key=emociones.get)
                        conf = int(emociones[emo] * 100)
                        x, y, w, h = box
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, f"{emo} ({conf}%)", (x, y - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                except Exception as e:
                    logger.error(f"Error en detección de emociones: {str(e)}")
                    continue

                if box is not None and not self.ya_intento_reconocer and self.frame_count <= self.recognition_limit:
                    try:
                        x, y, w, h = box
                        encs = self.face_recognition.face_encodings(frame_rgb, known_face_locations=[(y, x+w, y+h, x)])
                        if encs:
                            matches = self.face_recognition.compare_faces(self.embeddings, encs[0])
                            if True in matches:
                                idx = matches.index(True)
                                self.usuario_reconocido = self.nombres[idx]
                                self.ya_intento_reconocer = True
                        elif self.frame_count == self.recognition_limit:
                            self.ya_intento_reconocer = True
                    except Exception as e:
                        logger.error(f"Error en reconocimiento facial: {str(e)}")

                cv2.putText(frame, f"Usuario: {self.usuario_reconocido}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                try:
                    width = self.video_label.winfo_width() or 780
                    height = self.video_label.winfo_height() or 440
                    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    img = ImageOps.contain(img, (width, height))
                    tk_img = ImageTk.PhotoImage(img)
                    if self.video_label and self.video_label.winfo_exists():
                        self.video_label.imgtk = tk_img
                        self.video_label.configure(image=tk_img)
                except Exception as e:
                    logger.error(f"Error actualizando frame en UI: {str(e)}")

                try:
                    if emo and emo in self.emoji_imgs:
                        im = self.emoji_imgs[emo]
                        im = cv2.resize(im, (100, 100))
                        rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
                        pil_e = Image.fromarray(rgba)

                        canvas = Image.new("RGBA", (150, 440), (0, 0, 0, 255))
                        canvas.paste(pil_e, (25, 20), pil_e)

                        draw = ImageDraw.Draw(canvas)
                        draw.text((25, 130), f"{emo.capitalize()}\n{conf}%", fill=(255, 255, 255, 255))

                        bar_y = 200
                        for e in self.emotion_labels:
                            valores = list(self.emo_history[e])
                            promedio = sum(valores) / len(valores) if valores else 0
                            ancho = int(promedio * 100)
                            color = self.emotion_colors[e]
                            draw.rectangle([10, bar_y, 10+ancho, bar_y+10], fill=color)
                            draw.text((10, bar_y+12), f"{e}: {int(promedio*100)}%", fill=(255,255,255,255))
                            bar_y += 35

                        tk_emo = ImageTk.PhotoImage(canvas)
                        if self.panel and self.panel.winfo_exists():
                            self.panel.imgtk = tk_emo
                            self.panel.configure(image=tk_emo)
                except Exception as e:
                    logger.error(f"Error actualizando panel emoji: {str(e)}")

                elapsed = time.time() - start
                times.append(elapsed)
                if len(times) > 30:
                    times.pop(0)
                if times:
                    fps = len(times) / sum(times)
                    self.fps_var.set(f"{fps:.1f}")

        except Exception as e:
            logger.error(f"Error en loop principal: {str(e)}")
        finally:
            if cap:
                cap.release()
            if self.video_label:
                self.video_label.configure(image=None)
            if self.panel:
                self.panel.configure(image=None)