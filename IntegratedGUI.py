import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont
import threading
import cv2
from deepface import DeepFace
from fer import FER
import os
import sys

class EmotionDashboard:
    def __init__(self, root):
        # CAMBIO: ruta base al empaquetar con PyInstaller / auto-py-to-exe
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_path, 'data')

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

        tk.Label(
            self.menu_frame,
            text="MODELO",
            bg="#2c3e50",
            fg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=(20, 5))

        ttk.Radiobutton(self.menu_frame, text="FER", variable=self.selected_model, value="FER").pack(pady=5)
        ttk.Radiobutton(self.menu_frame, text="DeepFace", variable=self.selected_model, value="DeepFace").pack(pady=5)

        ttk.Button(self.menu_frame, text="Iniciar", command=self.iniciar).pack(pady=(20, 10))
        ttk.Button(self.menu_frame, text="Detener", command=self.detener).pack(pady=5)
        ttk.Button(self.menu_frame, text="Salir", command=self.root.quit).pack(pady=5)

        # CAMBIO: carga del logo desde data/
        try:
            logo_path = os.path.join(self.data_path, "logo_universidad.png")
            logo = Image.open(logo_path)
            logo = logo.resize((80, 80), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            tk.Label(self.menu_frame, image=self.logo_img, bg="#2c3e50")\
              .pack(side="bottom", pady=10)
        except Exception as e:
            print("[ERROR] Logo no cargado:", e)

        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(side="right", expand=True, fill="both")

        tk.Label(
            self.main_frame,
            text="Sistema de Detección de Emociones",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg="#34495e"
        ).pack(pady=10)

        self.video_area = tk.Frame(self.main_frame, bg="white")
        self.video_area.pack(fill="both", expand=True)

        self.video_label = tk.Label(self.video_area, bg="white")
        self.video_label.pack(side="left", expand=True, fill="both")

        self.emoji_panel = tk.Label(self.video_area, bg="black", width=150)
        self.emoji_panel.pack(side="right", fill="y")

    def iniciar(self):
        self.running = True
        modelo = self.selected_model.get()
        threading.Thread(target=self.detectar_emociones, args=(modelo,), daemon=True).start()

    def detener(self):
        self.running = False

    def detectar_emociones(self, modelo):
        cap = cv2.VideoCapture(0)

        # CAMBIO: rutas a recursos en data/
        emoji_path = os.path.join(self.data_path, "img")
        cascade_src = os.path.join(self.data_path, "haarcascade_frontalface_default.xml")

        # carga de emojis
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
        for emo, fname in emojis.items():
            p = os.path.join(emoji_path, fname)
            img = cv2.imread(p, cv2.IMREAD_UNCHANGED)
            if img is not None:
                emoji_imgs[emo] = img

        # CAMBIO: configuración de detectores
        if modelo == "FER":
            detector = FER(mtcnn=True)#optar por true o false dependiendo de la GPU y el rendimiento
        else:
            # redirige la búsqueda del cascade de OpenCV a data/
            if os.path.exists(cascade_src):
                cv2.data.haarcascades = self.data_path + os.sep
            else:
                print(f"[ERROR] Cascade no encontrado en: {cascade_src}")
            detector = None

        while self.running:
            ret, frame = cap.read()
            if not ret:
                break

            detected_emotion = ""
            confidence = 0

            try:
                if modelo == "FER":
                    faces = detector.detect_emotions(frame)
                    for face in faces:
                        (x, y, w, h) = face["box"]
                        best = max(face["emotions"], key=face["emotions"].get)
                        conf = int(face["emotions"][best] * 100)
                        detected_emotion = best
                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                        cv2.putText(
                            frame,
                            f"{best} ({conf}%)",
                            (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (255,0,0),
                            2
                        )
                else:
                    result = DeepFace.analyze(
                        frame,
                        actions=['emotion'],
                        enforce_detection=False
                    )[0]
                    emo = result['dominant_emotion']
                    conf = int(result['emotion'][emo])
                    detected_emotion = emo
                    x, y, w, h = (result['region'][k] for k in ('x','y','w','h'))
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
                    cv2.putText(
                        frame,
                        f"{emo} ({conf}%)",
                        (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255,0,0),
                        2
                    )
            except Exception as e:
                print("Error en detección:", e)

            # render video
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            pil = ImageOps.contain(pil, (780, 440))
            tk_img = ImageTk.PhotoImage(pil)
            self.video_label.imgtk = tk_img
            self.video_label.configure(image=tk_img)

            # render emoji
            if detected_emotion in emoji_imgs:
                emo_img = emoji_imgs[detected_emotion]
                emo_r = cv2.resize(emo_img, (100,100))
                emo_rgba = cv2.cvtColor(emo_r, cv2.COLOR_BGRA2RGBA)
                pil_emo = Image.fromarray(emo_rgba)
                canvas = Image.new("RGBA", (150,440), (0,0,0,255))
                canvas.paste(pil_emo, (25,150), pil_emo)

                draw = ImageDraw.Draw(canvas)
                font = ImageFont.load_default()
                text = f"{detected_emotion.capitalize()}\n{conf}%"
                draw.text((30, 270), text, font=font, fill=(255,255,255,255))

                tk_emo = ImageTk.PhotoImage(canvas)
                self.emoji_panel.imgtk = tk_emo
                self.emoji_panel.configure(image=tk_emo)

        cap.release()
        self.video_label.configure(image="")
        self.emoji_panel.configure(image="")

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionDashboard(root)
    root.mainloop()

#Maycol Acuña Diaz
