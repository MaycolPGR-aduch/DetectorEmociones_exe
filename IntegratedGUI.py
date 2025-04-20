import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps
import threading
import cv2
from deepface import DeepFace
from fer import FER
import os
import numpy as np

class EmotionDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Detección de Emociones")
        self.root.geometry("1000x600")
        self.root.configure(bg='#f4f4f4')

        self.running = False
        self.selected_model = tk.StringVar(value="FER")

        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

        self.menu_frame = tk.Frame(self.root, bg="#2c3e50", width=200)
        self.menu_frame.pack(side="left", fill="y")

        tk.Label(self.menu_frame, text="MODELO", bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        ttk.Radiobutton(self.menu_frame, text="FER", variable=self.selected_model, value="FER").pack(pady=5)
        ttk.Radiobutton(self.menu_frame, text="DeepFace", variable=self.selected_model, value="DeepFace").pack(pady=5)

        ttk.Button(self.menu_frame, text="Iniciar", command=self.iniciar).pack(pady=(20, 10))
        ttk.Button(self.menu_frame, text="Detener", command=self.detener).pack(pady=5)
        ttk.Button(self.menu_frame, text="Salir", command=self.root.quit).pack(pady=5)

        try:
            logo = Image.open("logo_universidad.png")
            logo = logo.resize((80, 80), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            tk.Label(self.menu_frame, image=self.logo_img, bg="#2c3e50").pack(side="bottom", pady=10)
        except Exception as e:
            print("[ERROR] Logo no cargado:", e)

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(side="right", expand=True, fill="both")

        self.title_label = tk.Label(self.main_frame, text="Sistema de Detección de Emociones", font=("Segoe UI", 20, "bold"), bg="white", fg="#34495e")
        self.title_label.pack(pady=10)

        self.video_area = tk.Frame(self.main_frame, bg="white")
        self.video_area.pack(fill="both", expand=True)

        self.video_label = tk.Label(self.video_area, bg="white")
        self.video_label.pack(side="left", expand=True, fill="both")

        self.emoji_panel = tk.Label(self.video_area, bg="black", width=150)
        self.emoji_panel.pack(side="right", fill="y")

    def iniciar(self):
        self.running = True
        modelo = self.selected_model.get()
        threading.Thread(target=self.detectar_emociones, args=(modelo,)).start()

    def detener(self):
        self.running = False

    def detectar_emociones(self, modelo):
        cap = cv2.VideoCapture(0)
        emoji_path = "img"
        emojis = {
            "angry": "angry.png",
            "disgust": "disgust.png",
            "fear": "fear.png",
            "happy": "happy.png",
            "sad": "sad.png",
            "surprise": "surprise.png",
            "neutral": "neutral.png"
        }

        emoji_imgs = {}
        for emotion, filename in emojis.items():
            path = os.path.join(emoji_path, filename)
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                emoji_imgs[emotion] = img

        detector = FER(mtcnn=False) if modelo == "FER" else None

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            detected_emotion = ""
            confidence = 0
            try:
                if modelo == "FER":
                    emociones = detector.detect_emotions(frame)
                    for face in emociones:
                        (x, y, w, h) = face["box"]
                        emociones_detectadas = face["emotions"]
                        emocion_principal = max(emociones_detectadas, key=emociones_detectadas.get)
                        confianza = emociones_detectadas[emocion_principal] * 100
                        detected_emotion = emocion_principal
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, f"{emocion_principal} ({int(confianza)}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
                else:
                    result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)[0]
                    emotion_scores = result['emotion']
                    emotion = result['dominant_emotion']
                    detected_emotion = emotion
                    confidence = emotion_scores[emotion]
                    x, y, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{emotion} ({int(confidence)}%)", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
            except Exception as e:
                print("Error:", e)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(rgb_frame)
            img_pil = ImageOps.contain(img_pil, (780, 440))
            imgtk = ImageTk.PhotoImage(image=img_pil)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

            if detected_emotion in emoji_imgs:
                emoji = emoji_imgs[detected_emotion]
                emoji_resized = cv2.resize(emoji, (100, 100))
                emoji_img = cv2.cvtColor(emoji_resized, cv2.COLOR_BGRA2RGBA)
                emoji_pil = Image.fromarray(emoji_img)
                canvas = Image.new("RGBA", (150, 440), (0, 0, 0, 255))
                canvas.paste(emoji_pil, (25, 150), emoji_pil)

                # Texto de la emoción debajo
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.load_default()
                text = f"{detected_emotion.capitalize()}\n{int(confidence)}%"
                draw.text((30, 270), text, font=font, fill=(255, 255, 255, 255))

                emoji_display = ImageTk.PhotoImage(canvas)
                self.emoji_panel.imgtk = emoji_display
                self.emoji_panel.configure(image=emoji_display)

        cap.release()
        self.video_label.configure(image="")
        self.emoji_panel.configure(image="")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionDashboard(root)
    root.mainloop()

#Maycol Acuña Diaz
