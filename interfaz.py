# interfaz.py
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
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
logger = logging.getLogger("interfaz")

class EmotionDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Detección de Emociones")
        self.root.geometry("1000x600")
        self.root.configure(bg='#f4f4f4')
        self.root.state("zoomed")  #

        # Determinar ruta de datos
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.environ.get("DETECTOR_DATA_PATH", 
                               os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'))
        print(f"InterfazUI: Usando directorio de datos: {self.data_path}")
        
        logger.info(f"Usando directorio de datos: {self.data_path}")
        
        # Crear directorios si no existen
        os.makedirs(self.data_path, exist_ok=True)
        os.makedirs(os.path.join(self.data_path, "usuarios"), exist_ok=True)
        os.makedirs(os.path.join(self.data_path, "img"), exist_ok=True)

        # Variables globales
        self.use_hist_eq = tk.IntVar(value=1)
        self.fps_var = tk.StringVar(value="FPS: 0.0")
        self.faces_var = tk.StringVar(value="Rostros: 0")

        # Estilo de botones
        style = ttk.Style()
        style.configure("Start.TButton", foreground="white", background="#28a745")
        style.configure("Stop.TButton", foreground="white", background="#dc3545")
        style.configure("TButton", font=("Segoe UI", 10), padding=6)

        self._crear_gui()

        # Inicializar módulos con manejo de errores
        try:
            # Importar módulos dinámicamente para mejorar la robustez
            from face_recognition_wrapper import get_face_recognition
            from tensorflow_minimal import get_fer_detector
            
            # Inicializar comprobando si existe TensorFlow
            try:
                detector_fer = get_fer_detector()
                logger.info(f"Detector FER inicializado: {detector_fer.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error al cargar detector FER: {str(e)}")
            
            # Inicializar detector de emociones
            from detector import DetectorEmociones
            self.detector = DetectorEmociones(
                self.content_frame, self.emoji_panel,
                self.use_hist_eq, self.data_path,
                self.fps_var, self.faces_var
            )
            logger.info("Detector inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar detector: {str(e)}")
            messagebox.showerror(
                "Error", 
                f"Error al inicializar detector: {str(e)}\nAlgunas funciones pueden no estar disponibles."
            )
        
        # Inicializar encuesta
        try:
            from encuesta import EncuestaEmocional
            self.encuesta = EncuestaEmocional(self.content_frame, self.data_path, self.show_welcome)
            logger.info("Encuesta inicializada correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar encuesta: {str(e)}")
            self.encuesta = None
        
        # Inicializar registro
        try:
            from registro import RegistroUsuario
            self.registro = RegistroUsuario(self.content_frame, self.data_path, self.show_welcome)
            logger.info("Registro inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al inicializar registro: {str(e)}")
            self.registro = None

        self.show_welcome()

    def _crear_gui(self):
        # --- Panel lateral ---
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
        grp3.pack(fill="x", pady=(0, 10), padx=10)

        tk.Label(grp3, text="Ecualizar Histograma:", bg="#2c3e50", fg="white").pack(anchor="w", pady=(0, 5))
        ttk.Radiobutton(grp3, text="Sí", variable=self.use_hist_eq, value=1).pack(anchor="w")
        ttk.Radiobutton(grp3, text="No", variable=self.use_hist_eq, value=0).pack(anchor="w")

        stats = tk.LabelFrame(menu, text="Estadísticas", bg="#2c3e50", fg="white", padx=10, pady=10)
        stats.pack(fill="x", padx=10, pady=(0, 10))
        tk.Label(stats, textvariable=self.fps_var, bg="#2c3e50", fg="white").pack(anchor="w")
        tk.Label(stats, textvariable=self.faces_var, bg="#2c3e50", fg="white").pack(anchor="w")

        self.status_label = tk.Label(menu, text="Detenido", bg="#2c3e50", fg="yellow", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(pady=10)

        # --- Panel principal (zona blanca + emoji) ---
        main = tk.Frame(self.root, bg="white")
        main.pack(side="right", expand=True, fill="both")

        header = tk.Frame(main, bg="white")
        header.pack(fill="x", pady=10)

        header_center = tk.Frame(header, bg="white")
        header_center.pack(anchor="center")

        try:
            logo_path = os.path.join(self.data_path, "logo_universidad.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).resize((60, 60))
                self.logo_img = ImageTk.PhotoImage(logo_img)
                tk.Label(header_center, image=self.logo_img, bg="white").pack(side="left", padx=(0, 10))
                logger.info("Logo cargado correctamente")
            else:
                logger.warning(f"No se encontró el logo en {logo_path}")
        except Exception as e:
            logger.error(f"Error al cargar logo: {str(e)}")
            pass

        tk.Label(header_center, text="Sistema de Detección de Emociones",
                 font=("Segoe UI", 20, "bold"), bg="white", fg="#34495e").pack(side="left")

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
        self.emoji_panel.pack_forget()

        frame = tk.Frame(self.content_frame, bg="white")
        frame.pack(expand=True, fill="both")

        try:
            path_img = os.path.join(self.data_path, "bienvenida.png")
            if os.path.exists(path_img):
                bienvenida_img = Image.open(path_img).resize((300, 200))
                self.img_bienvenida = ImageTk.PhotoImage(bienvenida_img)
                tk.Label(frame, image=self.img_bienvenida, bg="white").pack(pady=(30, 10))
                logger.info("Imagen de bienvenida cargada correctamente")
            else:
                logger.warning(f"No se encontró imagen de bienvenida en {path_img}")
        except Exception as e:
            logger.error(f"Error al cargar imagen de bienvenida: {str(e)}")
            pass

        texto = (
            "¡Bienvenido al Sistema de Detección de Emociones!\n\n"
            "Este sistema puede reconocer expresiones faciales en tiempo real.\n"
            "Puedes iniciar el detector, completar una encuesta o registrar tu rostro.\n\n"
            "Usa el menú lateral para comenzar."
        )
        tk.Label(frame, text=texto, font=("Segoe UI", 12), bg="white", justify="center").pack(pady=10)

    def show_detector(self):
        try:
            self.emoji_panel.pack(side="right", fill="y")
            self.clear_content()
            if hasattr(self, 'detector'):
                self.detector.mostrar()
                logger.info("Detector mostrado correctamente")
            else:
                messagebox.showerror("Error", "El detector no está disponible")
                logger.error("No se pudo mostrar el detector porque no está inicializado")
        except Exception as e:
            logger.error(f"Error al mostrar detector: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar detector: {str(e)}")

    def show_survey(self):
        try:
            self.emoji_panel.pack(side="right", fill="y")
            self.clear_content()
            if hasattr(self, 'encuesta') and self.encuesta:
                self.encuesta.mostrar()
                logger.info("Encuesta mostrada correctamente")
            else:
                messagebox.showerror("Error", "La encuesta no está disponible")
                logger.error("No se pudo mostrar la encuesta porque no está inicializada")
        except Exception as e:
            logger.error(f"Error al mostrar encuesta: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar encuesta: {str(e)}")

    def show_registro(self):
        try:
            self.emoji_panel.pack(side="right", fill="y")
            self.detener()
            self.clear_content()
            if hasattr(self, 'registro') and self.registro:
                self.registro.mostrar()
                logger.info("Registro mostrado correctamente")
            else:
                messagebox.showerror("Error", "El registro no está disponible")
                logger.error("No se pudo mostrar el registro porque no está inicializado")
        except Exception as e:
            logger.error(f"Error al mostrar registro: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar registro: {str(e)}")

    def iniciar(self):
        try:
            self.status_label.config(text="Ejecutando", fg="lime")
            self.show_detector()
            if hasattr(self, 'detector'):
                self.detector.iniciar()
                logger.info("Detector iniciado correctamente")
            else:
                logger.error("No se pudo iniciar el detector porque no está inicializado")
        except Exception as e:
            logger.error(f"Error al iniciar detector: {str(e)}")
            messagebox.showerror("Error", f"Error al iniciar detector: {str(e)}")

    def detener(self):
        try:
            self.status_label.config(text="Detenido", fg="yellow")
            if hasattr(self, 'detector'):
                self.detector.detener()
                logger.info("Detector detenido correctamente")
            else:
                logger.error("No se pudo detener el detector porque no está inicializado")
        except Exception as e:
            logger.error(f"Error al detener detector: {str(e)}")

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = EmotionDashboard(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error crítico en la aplicación: {str(e)}")
        try:
            messagebox.showerror("Error crítico", f"La aplicación no pudo iniciarse: {str(e)}")
        except:
            print(f"ERROR CRÍTICO: {str(e)}")