# registro.py
import os
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import re
import time
import face_recognition

class RegistroUsuario:
    def __init__(self, parent, data_path, volver_callback):
        self.parent = parent
        self.data_path = data_path
        self.volver_callback = volver_callback

        self.frame = None
        self.nombre_var = tk.StringVar()
        self.cap = None
        self.stop_flag = False
        self.video_label = None
        self.thread = None

    def mostrar(self):
        # Limpiar si ya existía
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()

        self.frame = tk.Frame(self.parent, bg="white")
        self.frame.pack(expand=True, fill="both")
        self.nombre_var.set("")
        self.stop_flag = False

        self._construir_gui()

        self.cap = cv2.VideoCapture(0)
        self._iniciar_video()

    def ocultar(self):
        self.stop_flag = True
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.frame and self.frame.winfo_exists():
            self.frame.pack_forget()

    def _volver(self):
        self.ocultar()
        self.volver_callback()

    def _construir_gui(self):
        tk.Label(self.frame, text="Registro de Usuario", font=("Segoe UI", 16), bg="white").pack(pady=(10, 5))

        # Área superior: nombre + botones
        top = tk.Frame(self.frame, bg="white")
        top.pack(pady=10)

        tk.Label(top, text="Nombre completo:", bg="white").pack(side="left", padx=(0, 10))
        tk.Entry(top, textvariable=self.nombre_var, width=25).pack(side="left")

        ttk.Button(top, text="Guardar y Capturar", command=self._guardar_y_capturar).pack(side="left", padx=10)
        ttk.Button(top, text="Volver", command=self._volver).pack(side="left", padx=10)

        # Cámara debajo
        self.video_label = tk.Label(self.frame, bg="black", width=640, height=480)
        self.video_label.pack(pady=10)

    def _iniciar_video(self):
        def loop():
            while not self.stop_flag and self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if not ret:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb).resize((640, 480))
                tk_img = ImageTk.PhotoImage(pil)

                if self.video_label and self.video_label.winfo_exists():
                    self.video_label.imgtk = tk_img
                    self.video_label.configure(image=tk_img)
                time.sleep(0.03)
        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def _guardar_y_capturar(self):
        nombre = self.nombre_var.get().strip()
        if not nombre or not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ ]+$', nombre):
            messagebox.showerror("Error", "Por favor ingresa un nombre válido sin caracteres especiales.")
            return

        if not self.cap or not self.cap.isOpened():
            messagebox.showerror("Error", "La cámara no está disponible.")
            return

        carpeta = os.path.join(self.data_path, "usuarios", nombre.replace(" ", "_"))
        os.makedirs(carpeta, exist_ok=True)

        fotos_guardadas = 0
        intentos = 0

        while fotos_guardadas < 5 and intentos < 30:
            ret, frame = self.cap.read()
            if not ret:
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            faces = face_recognition.face_locations(rgb)

            if faces:
                ruta = os.path.join(carpeta, f"{fotos_guardadas}.jpg")
                cv2.imwrite(ruta, frame)
                fotos_guardadas += 1
                time.sleep(0.5)

            intentos += 1

        if fotos_guardadas >= 5:
            messagebox.showinfo("Registro exitoso", f"Usuario '{nombre}' registrado correctamente.")
            self._volver()
        else:
            messagebox.showwarning("Falló", "No se detectó el rostro con claridad. Intenta de nuevo.")



