# detector.py
import threading
import cv2
import os
import numpy as np
import time
from PIL import Image, ImageTk, ImageOps, ImageDraw
from fer import FER
from deepface import DeepFace
import face_recognition
import tkinter as tk

class DetectorEmociones:
    def __init__(self, parent, panel_emoji, model_choice, hist_eq_var, data_path):
        self.parent = parent
        self.panel = panel_emoji
        self.model_choice = model_choice
        self.hist_eq_var = hist_eq_var
        self.data_path = data_path

        self.running = False
        self.thread = None
        self.video_label = None

        self.frame_count = 0
        self.recognition_limit = 25  # 25 frames ~5 segundos
        self.usuario_reconocido = "Desconocido"
        self.ya_intento_reconocer = False

        self.detector_fer = FER(mtcnn=False)
        self.last_emotion = None
        self.last_conf = 0

        self.emoji_imgs = self._cargar_emojis()
        self.embeddings = []
        self.nombres = []
        self._cargar_rostros()

    def _cargar_emojis(self):
        etiquetas = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
        imgs = {}
        for emo in etiquetas:
            ruta = os.path.join(self.data_path, "img", f"{emo}.png")
            img = cv2.imread(ruta, cv2.IMREAD_UNCHANGED)
            if img is not None:
                imgs[emo] = img
        return imgs

    def _cargar_rostros(self):
        base = os.path.join(self.data_path, "usuarios")
        if not os.path.exists(base):
            return
        for user in os.listdir(base):
            carpeta = os.path.join(base, user)
            for img_file in os.listdir(carpeta):
                img_path = os.path.join(carpeta, img_file)
                try:
                    img = face_recognition.load_image_file(img_path)
                    encs = face_recognition.face_encodings(img)
                    if encs:
                        self.embeddings.append(encs[0])
                        self.nombres.append(user.replace("_", " "))
                except:
                    continue

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

    def detener(self):
        self.running = False

    def _loop(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.frame_count = 0
        self.usuario_reconocido = "Desconocido"
        self.ya_intento_reconocer = False

        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            self.frame_count += 1
            modelo = self.model_choice.get()
            usar_hist = self.hist_eq_var.get()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            if usar_hist:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            emo, conf, box = None, 0, None

            try:
                if modelo == "FER":
                    faces = self.detector_fer.detect_emotions(frame)
                    if faces:
                        face = faces[0]
                        box = face["box"]
                        emociones = face["emotions"]
                        emo = max(emociones, key=emociones.get)
                        conf = int(emociones[emo] * 100)
                        x, y, w, h = box
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.putText(frame, f"{emo} ({conf}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.9, (255, 0, 0), 2)
                else:
                    result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)[0]
                    emo = result["dominant_emotion"]
                    conf = int(result["emotion"][emo])
                    box = result["region"].values()
                    x, y, w, h = box
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{emo} ({conf}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (255, 0, 0), 2)
            except Exception as e:
                pass

            # Reconocimiento facial (una sola vez o hasta el límite de frames)
            if box is not None and not self.ya_intento_reconocer and self.frame_count <= self.recognition_limit:
                x, y, w, h = box
                encs = face_recognition.face_encodings(frame_rgb, known_face_locations=[(y, x+w, y+h, x)])
                if encs:
                    matches = face_recognition.compare_faces(self.embeddings, encs[0])
                    if True in matches:
                        idx = matches.index(True)
                        self.usuario_reconocido = self.nombres[idx]
                        self.ya_intento_reconocer = True
                elif self.frame_count == self.recognition_limit:
                    self.ya_intento_reconocer = True

            # Mostrar etiqueta del usuario
            cv2.putText(frame, f"Usuario: {self.usuario_reconocido}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            # Mostrar video en GUI
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            img = ImageOps.contain(img, (780, 440))
            tk_img = ImageTk.PhotoImage(img)
            if self.video_label and self.video_label.winfo_exists():
                self.video_label.imgtk = tk_img
                self.video_label.configure(image=tk_img)

            # Mostrar emoji si cambia
            if emo and emo != self.last_emotion and emo in self.emoji_imgs:
                im = self.emoji_imgs[emo]
                im = cv2.resize(im, (100, 100))
                rgba = cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
                pil_e = Image.fromarray(rgba)
                canvas = Image.new("RGBA", (150, 440), (0, 0, 0, 255))
                canvas.paste(pil_e, (25, 150), pil_e)
                draw = ImageDraw.Draw(canvas)
                draw.text((30, 270), f"{emo.capitalize()}\n{conf}%", fill=(255, 255, 255, 255))
                tk_emo = ImageTk.PhotoImage(canvas)
                if self.panel and self.panel.winfo_exists():
                    self.panel.imgtk = tk_emo
                    self.panel.configure(image=tk_emo)
                self.last_emotion = emo
                self.last_conf = conf

        cap.release()
        if self.video_label:
            self.video_label.configure(image=None)
        if self.panel:
            self.panel.configure(image=None)
