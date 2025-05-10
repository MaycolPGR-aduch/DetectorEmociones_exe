import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageFont
import threading
import cv2
from fer import FER
import numpy as np
import os
import sys
import time
from collections import Counter
import csv
import os
import tkinter as tk
from tkinter import ttk, messagebox

class EmotionDashboard:
    def __init__(self, root):
        # ---- Ruta base (compatible con PyInstaller) ----
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_path, 'data')

        # ---- Configuración de ventana ----
        self.root = root
        self.root.title("Sistema de Detección de Emociones")
        self.root.geometry("1000x600")
        self.root.configure(bg='#f4f4f4')
        style = ttk.Style()
        style.configure("Start.TButton", foreground="white", background="#28a745")
        style.configure("Stop.TButton", foreground="white", background="#dc3545")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

        # ---- Variables ----
        self.running = False
        self.use_hist_eq = tk.IntVar(value=1)
        self.smoothing_window = 5
        self.last_emotions = []
        self.frame_times = []

        # ---- Menú izquierdo ----
        menu = tk.Frame(self.root, bg="#2c3e50", width=250)
        menu.pack(side="left", fill="y")

        # Grupo 1: Iniciar/Detener
        grp1 = tk.LabelFrame(menu, text="Control", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp1.pack(fill="x", pady=(20, 10), padx=10)
        ttk.Button(grp1, text="Iniciar", style="Start.TButton", command=self.iniciar).pack(fill="x", pady=5)
        ttk.Button(grp1, text="Detener", style="Stop.TButton", command=self.detener).pack(fill="x", pady=5)

        # Grupo 2: Detector/Encuesta
        grp2 = tk.LabelFrame(menu, text="Vistas", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp2.pack(fill="x", pady=(0, 10), padx=10)
        ttk.Button(grp2, text="Detector", command=self.show_detector).pack(fill="x", pady=5)
        ttk.Button(grp2, text="Encuesta", command=self.show_survey).pack(fill="x", pady=5)

        # Grupo 3: Opciones, Estado, Estadísticas
        grp3 = tk.LabelFrame(menu, text="Opciones y Estado", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp3.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(grp3, text="Ecualizar Histograma:", bg="#2c3e50", fg="white").pack(anchor="w")
        ttk.Radiobutton(grp3, text="Sí", variable=self.use_hist_eq, value=1).pack(anchor="w")
        ttk.Radiobutton(grp3, text="No", variable=self.use_hist_eq, value=0).pack(anchor="w")

        status_f = tk.LabelFrame(grp3, text="Estado", bg="#2c3e50", fg="white", padx=5, pady=5)
        status_f.pack(fill="x", pady=(10, 5))
        self.status_label = tk.Label(status_f, text="Detenido", bg="#2c3e50", fg="yellow")
        self.status_label.pack()

        stats_f = tk.LabelFrame(grp3, text="Estadísticas", bg="#2c3e50", fg="white", padx=5, pady=5)
        stats_f.pack(fill="x")
        self.fps_label = tk.Label(stats_f, text="FPS: 0.0", bg="#2c3e50", fg="white")
        self.fps_label.pack(anchor="w")
        self.face_count_label = tk.Label(stats_f, text="Rostros: 0", bg="#2c3e50", fg="white")
        self.face_count_label.pack(anchor="w")

        # ---- Panel principal ----
        main = tk.Frame(self.root, bg="white")
        main.pack(side="right", expand=True, fill="both")

        # Logo junto al título
        header = tk.Frame(main, bg="white")
        header.pack(fill="x", pady=10)
        try:
            logo = Image.open(os.path.join(self.data_path, "logo_universidad.png")).resize((60,60), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            tk.Label(header, image=self.logo_img, bg="white").pack(side="left", padx=(20,10))
        except:
            pass
        tk.Label(header, text="Sistema de Detección de Emociones", font=("Segoe UI",20,"bold"),
                 bg="white", fg="#34495e").pack(side="left")

        # Contenedor de contenido y emoji
        container = tk.Frame(main, bg="white")
        container.pack(expand=True, fill="both")

        # Frame de contenido (detector, encuesta o bienvenida)
        self.content_frame = tk.Frame(container, bg="white")
        self.content_frame.pack(side="left", expand=True, fill="both")

        # Panel emoji fijo a la derecha
        self.emoji_panel = tk.Label(container, bg="black", width=150)
        self.emoji_panel.pack(side="right", fill="y")

        # ---- Frames internos ----
        # Bienvenida
        self.welcome_frame = tk.Frame(self.content_frame, bg="white")
        tk.Label(self.welcome_frame, text="¡Bienvenido!\nEste sistema detecta tus emociones en tiempo real.\nSelecciona 'Iniciar' para comenzar o 'Encuesta' para registrar cómo te sientes.",
                 font=("Segoe UI",14), bg="white", justify="center").pack(expand=True)

        # Detector
        self.detector_frame = tk.Frame(self.content_frame, bg="white")
        self.video_label = tk.Label(self.detector_frame, bg="black")
        self.video_label.pack(expand=True, fill="both")

        # Encuesta
        self.survey_frame = tk.Frame(self.content_frame, bg="white")
        tk.Label(self.survey_frame, text="Encuesta de Emociones", font=("Segoe UI",16), bg="white").pack(pady=10)
        self.survey_var = tk.StringVar(value="neutral")
        for opt in ["happy","sad","angry","surprise","neutral"]:
            ttk.Radiobutton(self.survey_frame, text=opt.capitalize(), variable=self.survey_var, value=opt).pack(anchor="w", padx=20)
        ttk.Button(self.survey_frame, text="Enviar", command=self.enviar_encuesta).pack(pady=20)

        # Mostrar bienvenida inicialmente
        self.show_welcome()

        # ---- Carga de emojis ----
        self.emotion_labels = ["angry","disgust","fear","happy","sad","surprise","neutral"]
        self.emoji_imgs = {}
        for emo in self.emotion_labels:
            path = os.path.join(self.data_path, "img", f"{emo}.png")
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                self.emoji_imgs[emo] = img

        # ---- Detector FER ----
        self.detector = FER(mtcnn=False)

    def show_welcome(self):
        self.clear_content()
        self.welcome_frame.pack(expand=True, fill="both")

    def show_detector(self):
        self.clear_content()
        self.detector_frame.pack(expand=True, fill="both")

    def show_survey(self):
        self.clear_content()
        self.survey_frame.pack(expand=True, fill="both")

    def clear_content(self):
        self.welcome_frame.pack_forget()
        self.detector_frame.pack_forget()
        self.survey_frame.pack_forget()

    def iniciar(self):
        if not self.running:
            self.running = True
            self.status_label.config(text="Ejecutando", fg="lime")
            threading.Thread(target=self.detectar_emociones, daemon=True).start()
            self.show_detector()

    def detener(self):
        self.running = False
        self.status_label.config(text="Detenido", fg="yellow")

    def enviar_encuesta(self):
        print("Respuesta encuesta:", self.survey_var.get())

    def detectar_emociones(self):
        cap = cv2.VideoCapture(0)
        last_time = time.time()
        while self.running:
            start = time.time()
            ret, frame = cap.read()
            if not ret: break

            if self.use_hist_eq.get() == 1:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)
                frame = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            faces = self.detector.detect_emotions(frame)
            self.face_count_label.config(text=f"Rostros: {len(faces)}")

            emo, conf = None, 0
            if faces:
                box = faces[0]["box"]
                emotions = faces[0]["emotions"]
                best = max(emotions, key=emotions.get)
                conf = int(emotions[best] * 100)
                emo = best
                self.last_emotions.append(emo)
                if len(self.last_emotions) > self.smoothing_window:
                    self.last_emotions.pop(0)
                emo = Counter(self.last_emotions).most_common(1)[0][0]
                x,y,w,h = box
                cv2.rectangle(frame, (x,y), (x+w,y+h), (0,255,0), 2)
                cv2.putText(frame, f"{emo} ({conf}%)", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil = Image.fromarray(rgb)
            pil = ImageOps.contain(pil, (780, 440))
            tk_img = ImageTk.PhotoImage(pil)
            self.video_label.imgtk = tk_img
            self.video_label.configure(image=tk_img)

            # Emoji panel update
            if emo in self.emoji_imgs:
                img = self.emoji_imgs[emo]
                r = cv2.resize(img, (100,100))
                rgba = cv2.cvtColor(r, cv2.COLOR_BGRA2RGBA)
                pil_e = Image.fromarray(rgba)
                canvas = Image.new("RGBA", (150,440), (0,0,0,255))
                canvas.paste(pil_e, (25,150), pil_e)
                draw = ImageDraw.Draw(canvas)
                font = ImageFont.load_default()
                draw.text((30,270), f"{emo.capitalize()}\n{conf}%", font=font, fill=(255,255,255,255))
                tk_e = ImageTk.PhotoImage(canvas)
                self.emoji_panel.imgtk = tk_e
                self.emoji_panel.configure(image=tk_e)

            frame_time = time.time() - start
            self.frame_times.append(frame_time)
            if len(self.frame_times) > 30:
                self.frame_times.pop(0)
            if time.time() - last_time >= 1.0:
                fps = len(self.frame_times) / sum(self.frame_times)
                self.fps_label.config(text=f"FPS: {fps:.1f}")
                last_time = time.time()

        cap.release()
        self.video_label.configure(image=None)
        self.emoji_panel.configure(image=None)

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionDashboard(root)
    root.mainloop()