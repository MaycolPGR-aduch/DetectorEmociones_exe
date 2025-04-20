import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
from DE_Emoji import ejecutar_fer
from DE_DeepFace import ejecutar_deepface

class EmotionDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Detección de Emociones")
        self.root.geometry("800x500")
        self.root.configure(bg='#f4f4f4')

        # Estilo general
        style = ttk.Style()
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

        # Frame lateral (menú)
        self.menu_frame = tk.Frame(self.root, bg="#2c3e50", width=200)
        self.menu_frame.pack(side="left", fill="y")

        # Botones del menú
        self.modelo = tk.StringVar(value="FER")
        tk.Label(self.menu_frame, text="MODELO", bg="#2c3e50", fg="white", font=("Segoe UI", 10, "bold")).pack(pady=(20, 5))
        ttk.Radiobutton(self.menu_frame, text="FER", variable=self.modelo, value="FER").pack(pady=5)
        ttk.Radiobutton(self.menu_frame, text="DeepFace", variable=self.modelo, value="DeepFace").pack(pady=5)

        ttk.Button(self.menu_frame, text="Iniciar", command=self.iniciar).pack(pady=(20, 10))
        ttk.Button(self.menu_frame, text="Salir", command=self.root.quit).pack(pady=5)

        # Cargar y mostrar logo abajo a la izquierda
        try:
            logo = Image.open("logo_universidad.png")
            logo = logo.resize((80, 80), Image.ANTIALIAS)
            self.logo_img = ImageTk.PhotoImage(logo)
            logo_label = tk.Label(self.menu_frame, image=self.logo_img, bg="#2c3e50")
            logo_label.pack(side="bottom", pady=10)
        except Exception as e:
            print("[ERROR] Logo no cargado:", e)

        # Frame principal
        self.main_frame = tk.Frame(self.root, bg="white")
        self.main_frame.pack(side="right", expand=True, fill="both")

        self.title_label = tk.Label(self.main_frame, text="Sistema de Detección de Emociones", font=("Segoe UI", 20, "bold"), bg="white", fg="#34495e")
        self.title_label.pack(pady=40)

        self.status_label = tk.Label(self.main_frame, text="Seleccione un modelo en el menú lateral e inicie el sistema", font=("Segoe UI", 12), bg="white", fg="#7f8c8d")
        self.status_label.pack(pady=10)

    def iniciar(self):
        modelo = self.modelo.get()
        self.status_label.config(text=f"Iniciando modelo: {modelo}")

        def lanzar_modelo():
            if modelo == "FER":
                ejecutar_fer()
            elif modelo == "DeepFace":
                ejecutar_deepface()

        threading.Thread(target=lanzar_modelo).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionDashboard(root)
    root.mainloop()
