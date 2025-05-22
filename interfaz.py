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
        self.root.title("Sistema de Detección de Emociones - Universidad")
        self.root.geometry("1200x700")
        self.root.configure(bg='#f8f9fa')
        self.root.state("zoomed")

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

        # Configurar estilos modernos
        self._configurar_estilos()
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

    def _configurar_estilos(self):
        """Configurar estilos modernos para la aplicación"""
        style = ttk.Style()
        
        # Configurar tema base
        style.theme_use('clam')
        
        # Colores principales
        colors = {
            'primary': '#0d6efd',      # Azul moderno
            'success': '#198754',      # Verde éxito
            'danger': '#dc3545',       # Rojo peligro
            'warning': '#ffc107',      # Amarillo advertencia
            'info': '#0dcaf0',         # Cian información
            'light': '#f8f9fa',        # Gris claro
            'dark': '#212529',         # Gris oscuro
            'secondary': '#6c757d'     # Gris secundario
        }
        
        # Estilo para botones de acción principales
        style.configure("Primary.TButton",
                       background=colors['primary'],
                       foreground="white",
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 12),
                       relief="flat",
                       borderwidth=0)
        
        style.map("Primary.TButton",
                 background=[('active', '#0b5ed7'), ('pressed', '#0a58ca')])
        
        # Estilo para botón de inicio
        style.configure("Success.TButton",
                       background=colors['success'],
                       foreground="white",
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 12),
                       relief="flat",
                       borderwidth=0)
        
        style.map("Success.TButton",
                 background=[('active', '#157347'), ('pressed', '#146c43')])
        
        # Estilo para botón de detener
        style.configure("Danger.TButton",
                       background=colors['danger'],
                       foreground="white",
                       font=("Segoe UI", 11, "bold"),
                       padding=(20, 12),
                       relief="flat",
                       borderwidth=0)
        
        style.map("Danger.TButton",
                 background=[('active', '#bb2d3b'), ('pressed', '#b02a37')])
        
        # Estilo para botones secundarios
        style.configure("Secondary.TButton",
                       background=colors['light'],
                       foreground=colors['dark'],
                       font=("Segoe UI", 10),
                       padding=(15, 10),
                       relief="flat",
                       borderwidth=1)
        
        style.map("Secondary.TButton",
                 background=[('active', '#e9ecef'), ('pressed', '#dee2e6')])

    def _crear_iconos_texto(self):
        """Crear iconos usando texto Unicode para los botones"""
        return {
            'play': '▶',      # Iniciar
            'stop': '⏹',      # Detener
            'camera': '📷',    # Detector
            'survey': '📋',    # Encuesta
            'user': '👤',      # Registro
            'settings': '⚙',   # Configuración
            'stats': '📊'      # Estadísticas
        }

    def _crear_gui(self):
        # Obtener iconos
        icons = self._crear_iconos_texto()
        
        # --- Panel lateral mejorado con scroll ---
        menu_container = tk.Frame(self.root, bg="#1e293b", width=280)
        menu_container.pack(side="left", fill="y")
        menu_container.pack_propagate(False)
        
        # Canvas y scrollbar para el menú
        canvas = tk.Canvas(menu_container, bg="#1e293b", highlightthickness=0, width=280)
        scrollbar = ttk.Scrollbar(menu_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1e293b")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Usar scrollable_frame como menu
        menu = scrollable_frame
        
        # Título del menú
        title_frame = tk.Frame(menu, bg="#1e293b")
        title_frame.pack(fill="x", pady=(20, 30), padx=20)
        
        tk.Label(title_frame, 
                text="🎯 CONTROL PANEL", 
                font=("Segoe UI", 14, "bold"), 
                bg="#1e293b", 
                fg="#f1f5f9").pack()

        # Grupo de Control Principal
        grp1 = tk.LabelFrame(menu, 
                           text=f"{icons['settings']} Control Principal", 
                           bg="#1e293b", 
                           fg="#e2e8f0", 
                           font=("Segoe UI", 11, "bold"),
                           padx=15, 
                           pady=15)
        grp1.pack(fill="x", pady=(0, 20), padx=20)
        
        # Botón Iniciar con estilo mejorado
        btn_iniciar = ttk.Button(grp1, 
                               text=f"{icons['play']} Iniciar Detección", 
                               style="Success.TButton", 
                               command=self.iniciar)
        btn_iniciar.pack(fill="x", pady=(0, 10))
        
        # Botón Detener
        btn_detener = ttk.Button(grp1, 
                               text=f"{icons['stop']} Detener", 
                               style="Danger.TButton", 
                               command=self.detener)
        btn_detener.pack(fill="x")

        # Grupo de Navegación
        grp2 = tk.LabelFrame(menu, 
                           text="🧭 Navegación", 
                           bg="#1e293b", 
                           fg="#e2e8f0", 
                           font=("Segoe UI", 11, "bold"),
                           padx=15, 
                           pady=15)
        grp2.pack(fill="x", pady=(0, 20), padx=20)
        
        # Botones de navegación con iconos
        nav_buttons = [
            (f"{icons['camera']} Detector de Emociones", self.show_detector),
            (f"{icons['survey']} Encuesta Emocional", self.show_survey),
            (f"{icons['user']} Registrar Usuario", self.show_registro)
        ]
        
        for text, command in nav_buttons:
            btn = ttk.Button(grp2, text=text, style="Primary.TButton", command=command)
            btn.pack(fill="x", pady=(0, 8))

        # Grupo de Configuración
        grp3 = tk.LabelFrame(menu, 
                           text=f"{icons['settings']} Configuración", 
                           bg="#1e293b", 
                           fg="#e2e8f0", 
                           font=("Segoe UI", 11, "bold"),
                           padx=15, 
                           pady=15)
        grp3.pack(fill="x", pady=(0, 20), padx=20)

        # Frame para configuración de histograma
        hist_frame = tk.Frame(grp3, bg="#1e293b")
        hist_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(hist_frame, 
                text="🔧 Ecualizar Histograma:", 
                bg="#1e293b", 
                fg="#cbd5e1", 
                font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 5))
        
        radio_frame = tk.Frame(hist_frame, bg="#1e293b")
        radio_frame.pack(fill="x")
        
        ttk.Radiobutton(radio_frame, text="✓ Activado", variable=self.use_hist_eq, value=1).pack(anchor="w")
        ttk.Radiobutton(radio_frame, text="✗ Desactivado", variable=self.use_hist_eq, value=0).pack(anchor="w")

        # Estadísticas mejoradas
        stats = tk.LabelFrame(menu, 
                            text=f"{icons['stats']} Estadísticas", 
                            bg="#1e293b", 
                            fg="#e2e8f0", 
                            font=("Segoe UI", 11, "bold"),
                            padx=15, 
                            pady=15)
        stats.pack(fill="x", padx=20, pady=(0, 20))
        
        # Frame para estadísticas
        stats_content = tk.Frame(stats, bg="#1e293b")
        stats_content.pack(fill="x")
        
        tk.Label(stats_content, 
                textvariable=self.fps_var, 
                bg="#1e293b", 
                fg="#22d3ee", 
                font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=2)
        
        tk.Label(stats_content, 
                textvariable=self.faces_var, 
                bg="#1e293b", 
                fg="#34d399", 
                font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=2)

        # Indicador de estado mejorado
        status_frame = tk.Frame(menu, bg="#1e293b")
        status_frame.pack(pady=20, padx=20)
        
        tk.Label(status_frame, 
                text="Estado del Sistema:", 
                bg="#1e293b", 
                fg="#94a3b8", 
                font=("Segoe UI", 10)).pack()
        
        self.status_label = tk.Label(status_frame, 
                                   text="🔴 Sistema Detenido", 
                                   bg="#1e293b", 
                                   fg="#fbbf24", 
                                   font=("Segoe UI", 12, "bold"))
        self.status_label.pack(pady=(5, 0))
        
        # Espacio adicional al final para mejor scroll
        tk.Frame(menu, bg="#1e293b", height=50).pack()

        # --- Panel principal mejorado ---
        main = tk.Frame(self.root, bg="#ffffff")
        main.pack(side="right", expand=True, fill="both")

        # Header con gradiente visual
        header = tk.Frame(main, bg="#ffffff", height=100)
        header.pack(fill="x", pady=(0, 0))
        header.pack_propagate(False)

        # Contenedor centrado para el header
        header_center = tk.Frame(header, bg="#ffffff")
        header_center.pack(expand=True)

        # Logo y título
        title_container = tk.Frame(header_center, bg="#ffffff")
        title_container.pack(expand=True, pady=20)

        try:
            logo_path = os.path.join(self.data_path, "logo_universidad.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path).resize((70, 70))
                self.logo_img = ImageTk.PhotoImage(logo_img)
                tk.Label(title_container, image=self.logo_img, bg="#ffffff").pack(side="left", padx=(0, 15))
                logger.info("Logo cargado correctamente")
            else:
                # Logo placeholder si no existe
                logo_placeholder = tk.Label(title_container, 
                                          text="🎓", 
                                          font=("Segoe UI", 40), 
                                          bg="#ffffff", 
                                          fg="#0d6efd")
                logo_placeholder.pack(side="left", padx=(0, 15))
                logger.warning(f"No se encontró el logo en {logo_path}")
        except Exception as e:
            logger.error(f"Error al cargar logo: {str(e)}")
            pass

        # Título principal mejorado
        title_frame = tk.Frame(title_container, bg="#ffffff")
        title_frame.pack(side="left")
        
        tk.Label(title_frame, 
                text="Sistema de Detección de Emociones",
                font=("Segoe UI", 24, "bold"), 
                bg="#ffffff", 
                fg="#1e293b").pack()
        
        tk.Label(title_frame, 
                text="Tecnología Avanzada de Reconocimiento Facial",
                font=("Segoe UI", 12), 
                bg="#ffffff", 
                fg="#64748b").pack()

        # Línea separadora
        separator = tk.Frame(main, bg="#e2e8f0", height=2)
        separator.pack(fill="x")

        # Contenedor principal
        container = tk.Frame(main, bg="#ffffff")
        container.pack(expand=True, fill="both")

        self.content_frame = tk.Frame(container, bg="#ffffff")
        self.content_frame.pack(side="left", expand=True, fill="both")

        self.emoji_panel = tk.Label(container, bg="#000000", width=150)
        self.emoji_panel.pack(side="right", fill="y")

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.pack_forget()

    def show_welcome(self):
        self.clear_content()
        self.emoji_panel.pack_forget()

        # Container principal para bienvenida
        main_container = tk.Frame(self.content_frame, bg="#ffffff")
        main_container.pack(expand=True, fill="both")

        # Frame centrado
        welcome_frame = tk.Frame(main_container, bg="#ffffff")
        welcome_frame.pack(expand=True)

        try:
            path_img = os.path.join(self.data_path, "bienvenida.png")
            if os.path.exists(path_img):
                bienvenida_img = Image.open(path_img).resize((400, 250))
                self.img_bienvenida = ImageTk.PhotoImage(bienvenida_img)
                tk.Label(welcome_frame, image=self.img_bienvenida, bg="#ffffff").pack(pady=(40, 20))
                logger.info("Imagen de bienvenida cargada correctamente")
            else:
                # Placeholder visual si no existe la imagen
                placeholder = tk.Label(welcome_frame, 
                                     text="🤖🧠💡", 
                                     font=("Segoe UI", 80), 
                                     bg="#ffffff", 
                                     fg="#0d6efd")
                placeholder.pack(pady=(40, 20))
                logger.warning(f"No se encontró imagen de bienvenida en {path_img}")
        except Exception as e:
            logger.error(f"Error al cargar imagen de bienvenida: {str(e)}")
            pass

        # Mensaje de bienvenida mejorado
        welcome_title = tk.Label(welcome_frame, 
                               text="¡Bienvenido al Futuro de la Detección Emocional!", 
                               font=("Segoe UI", 22, "bold"), 
                               bg="#ffffff", 
                               fg="#1e293b")
        welcome_title.pack(pady=(0, 15))

        # Subtítulo
        subtitle = tk.Label(welcome_frame, 
                          text="Tecnología de Vanguardia para el Análisis de Expresiones Faciales", 
                          font=("Segoe UI", 14), 
                          bg="#ffffff", 
                          fg="#64748b")
        subtitle.pack(pady=(0, 25))

        # Descripción mejorada
        description_text = (
            "🎯 Nuestro sistema utiliza inteligencia artificial avanzada para detectar y analizar\n"
            "   emociones humanas en tiempo real con precisión excepcional.\n\n"
            "🚀 Características principales:\n"
            "   • Reconocimiento facial en tiempo real\n"
            "   • Análisis de múltiples emociones simultáneamente\n"
            "   • Interfaz intuitiva y profesional\n"
            "   • Registro y seguimiento de usuarios\n\n"
            "💡 Para comenzar, utiliza el panel de control lateral y selecciona la función deseada."
        )
        
        description = tk.Label(welcome_frame, 
                             text=description_text, 
                             font=("Segoe UI", 12), 
                             bg="#ffffff", 
                             fg="#334155",
                             justify="left")
        description.pack(pady=(0, 30))

        # Botones de acceso rápido
        quick_actions = tk.Frame(welcome_frame, bg="#ffffff")
        quick_actions.pack(pady=(0, 20))

        tk.Label(quick_actions, 
                text="Acciones Rápidas:", 
                font=("Segoe UI", 14, "bold"), 
                bg="#ffffff", 
                fg="#1e293b").pack(pady=(0, 15))

        buttons_frame = tk.Frame(quick_actions, bg="#ffffff")
        buttons_frame.pack()

        # Botones de acceso rápido
        ttk.Button(buttons_frame, 
                  text="🚀 Iniciar Detección", 
                  style="Success.TButton", 
                  command=self.iniciar).pack(side="left", padx=(0, 10))

        ttk.Button(buttons_frame, 
                  text="📋 Hacer Encuesta", 
                  style="Primary.TButton", 
                  command=self.show_survey).pack(side="left", padx=(0, 10))

        ttk.Button(buttons_frame, 
                  text="👤 Registrarse", 
                  style="Secondary.TButton", 
                  command=self.show_registro).pack(side="left")

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
            self.status_label.config(text="🟢 Sistema Activo", fg="#22c55e")
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
            self.status_label.config(text="🔴 Sistema Detenido", fg="#fbbf24")
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