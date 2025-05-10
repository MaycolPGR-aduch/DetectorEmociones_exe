# interfaz.py
import os
import sys
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk

from detector import DetectorEmociones
from encuesta import EncuestaEmocional
from registro import RegistroUsuario

class EmotionDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Detección de Emociones")
        self.root.geometry("1000x600")
        self.root.configure(bg='#f4f4f4')

        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_path, 'data')

        self.model_choice = tk.StringVar(value="FER")
        self.use_hist_eq = tk.IntVar(value=1)

        style = ttk.Style()
        style.configure("Start.TButton", foreground="white", background="#28a745")
        style.configure("Stop.TButton", foreground="white", background="#dc3545")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

        self._crear_gui()

        # Subcomponentes (Detector, Encuesta, Registro)
        self.detector = DetectorEmociones(self.content_frame, self.emoji_panel,
                                          self.model_choice, self.use_hist_eq, self.data_path)
        self.encuesta = EncuestaEmocional(self.content_frame, self.data_path, self.show_welcome)
        self.registro = RegistroUsuario(self.content_frame, self.data_path, self.show_welcome)

        self.show_welcome()

    def _crear_gui(self):
        # Menú lateral
        menu = tk.Frame(self.root, bg="#2c3e50", width=250)
        menu.pack(side="left", fill="y")

        grp1 = tk.LabelFrame(menu, text="Control", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp1.pack(fill="x", pady=(20, 10), padx=10)
        ttk.Button(grp1, text="Iniciar", style="Start.TButton", command=self.iniciar).pack(fill="x", pady=5)
        ttk.Button(grp1, text="Detener", style="Stop.TButton", command=self.detener).pack(fill="x", pady=5)

        grp2 = tk.LabelFrame(menu, text="Vistas", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp2.pack(fill="x", pady=(0, 10), padx=10)
        ttk.Button(grp2, text="Detector", command=self.show_detector).pack(fill="x", pady=5)
        ttk.Button(grp2, text="Encuesta", command=self.show_survey).pack(fill="x", pady=5)
        ttk.Button(grp2, text="Registrar usuario", command=self.show_registro).pack(fill="x", pady=5)

        grp3 = tk.LabelFrame(menu, text="Configuración", bg="#2c3e50", fg="white", padx=10, pady=10)
        grp3.pack(fill="both", expand=True, pady=(0, 10), padx=10)
        tk.Label(grp3, text="Modelo:", bg="#2c3e50", fg="white").pack(anchor="w")
        ttk.Radiobutton(grp3, text="FER", variable=self.model_choice, value="FER").pack(anchor="w")
        ttk.Radiobutton(grp3, text="DeepFace", variable=self.model_choice, value="DeepFace").pack(anchor="w")

        tk.Label(grp3, text="Ecualizar Histograma:", bg="#2c3e50", fg="white").pack(anchor="w", pady=(10, 0))
        ttk.Radiobutton(grp3, text="Sí", variable=self.use_hist_eq, value=1).pack(anchor="w")
        ttk.Radiobutton(grp3, text="No", variable=self.use_hist_eq, value=0).pack(anchor="w")

        status_f = tk.LabelFrame(grp3, text="Estado", bg="#2c3e50", fg="white", padx=5, pady=5)
        status_f.pack(fill="x", pady=(10, 5))
        self.status_label = tk.Label(status_f, text="Detenido", bg="#2c3e50", fg="yellow")
        self.status_label.pack()

        # Panel principal
        main = tk.Frame(self.root, bg="white")
        main.pack(side="right", expand=True, fill="both")

        header = tk.Frame(main, bg="white")
        header.pack(fill="x", pady=10)
        try:
            logo_path = os.path.join(self.data_path, "logo_universidad.png")
            logo_img = Image.open(logo_path).resize((60, 60))
            self.logo_img = ImageTk.PhotoImage(logo_img)
            tk.Label(header, image=self.logo_img, bg="white").pack(side="left", padx=(20, 10))
        except:
            pass
        tk.Label(header, text="Sistema de Detección de Emociones", font=("Segoe UI", 20, "bold"),
                 bg="white", fg="#34495e").pack(side="left")

        container = tk.Frame(main, bg="white")
        container.pack(expand=True, fill="both")

        self.content_frame = tk.Frame(container, bg="white")
        self.content_frame.pack(side="left", expand=True, fill="both")

        self.emoji_panel = tk.Label(container, bg="black", width=150)
        self.emoji_panel.pack(side="right", fill="y")

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.pack_forget()

    def show_welcome(self):
        self.clear_content()
        frame = tk.Frame(self.content_frame, bg="white")
        frame.pack(expand=True, fill="both")
        tk.Label(frame, text="\u00a1Bienvenido!\nEste sistema detecta tus emociones en tiempo real.\nPresiona 'Iniciar' o explora las funciones del menú.",
                 font=("Segoe UI", 14), bg="white", justify="center").pack(expand=True)

    def show_detector(self):
        self.clear_content()
        self.detector.mostrar()

    def show_survey(self):
        self.clear_content()
        self.encuesta.mostrar()

    def show_registro(self):
        self.detener()
        self.clear_content()
        self.registro.mostrar()

    def iniciar(self):
        self.status_label.config(text="Ejecutando", fg="lime")
        self.show_detector()
        self.detector.iniciar()

    def detener(self):
        self.status_label.config(text="Detenido", fg="yellow")
        self.detector.detener()

if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionDashboard(root)
    root.mainloop()
