# encuesta.py
import tkinter as tk
from tkinter import ttk, messagebox
import time
import os
import csv
import logging

# Importar config.py
from config import DATA_DIR

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("encuesta")

class EncuestaEmocional:
    def __init__(self, parent_frame, data_path, on_submit_callback):
        self.parent = parent_frame
        self.data_path = data_path
        # Verificar si la ruta data_path es consistente con DATA_DIR
        if data_path != DATA_DIR:
            logger.warning(f"Inconsistencia de rutas: data_path={data_path}, DATA_DIR={DATA_DIR}")
        
        self.on_submit = on_submit_callback

        self.name_var = tk.StringVar()
        self.email_var = tk.StringVar()
        self.preg1_var = tk.StringVar(value="neutral")
        self.preg2_var = tk.IntVar(value=5)
        self.preg3_var = tk.StringVar()
        
        self.frame = None
        logger.info("Encuesta inicializada correctamente")

    def mostrar(self):
        try:
            if hasattr(self, "frame") and self.frame and self.frame.winfo_exists():
                self.frame.destroy()

            self.frame = tk.Frame(self.parent, bg="white")

            tk.Label(self.frame, text="Encuesta de Emociones", font=("Segoe UI", 16, "bold"), bg="white", fg="#34495e") \
                .pack(pady=(10,5))

            form = tk.Frame(self.frame, bg="white")
            form.pack(fill="both", expand=True, padx=30, pady=10)

            tk.Label(form, text="Nombre:", bg="white", anchor="w").pack(anchor="w")
            ttk.Entry(form, textvariable=self.name_var, width=40).pack(fill="x", pady=3)

            tk.Label(form, text="Correo electrónico:", bg="white", anchor="w").pack(anchor="w", pady=(10,0))
            ttk.Entry(form, textvariable=self.email_var, width=40).pack(fill="x", pady=3)

            tk.Label(form, text="1) ¿Cuál es tu emoción principal ahora?", bg="white", anchor="w", font=("Segoe UI", 10, "bold"))\
                .pack(anchor="w", pady=(15, 2))
            for emo in ["happy", "sad", "angry", "surprise", "neutral"]:
                ttk.Radiobutton(form, text=emo.capitalize(), variable=self.preg1_var, value=emo).pack(anchor="w")

            tk.Label(form, text="2) ¿Con qué intensidad la sientes? (1 a 10)", bg="white", anchor="w", font=("Segoe UI", 10, "bold")) \
                .pack(anchor="w", pady=(15,2))
            ttk.Scale(form, from_=1, to=10, orient="horizontal", variable=self.preg2_var).pack(fill="x")

            tk.Label(form, text="3) Describe brevemente por qué la sientes:", bg="white", anchor="w", font=("Segoe UI", 10, "bold")) \
                .pack(anchor="w", pady=(15,2))
            ttk.Entry(form, textvariable=self.preg3_var, width=60).pack(fill="x", pady=(0,10))

            ttk.Button(self.frame, text="Enviar respuestas", command=self.enviar_respuestas).pack(pady=10)
            self.frame.pack(expand=True, fill="both")
            
            logger.info("Encuesta mostrada correctamente")
        except Exception as e:
            logger.error(f"Error al mostrar encuesta: {str(e)}")
            messagebox.showerror("Error", f"Error al mostrar formulario de encuesta: {str(e)}")

    def enviar_respuestas(self):
        try:
            nombre = self.name_var.get().strip()
            email = self.email_var.get().strip()
            if not nombre or not email:
                messagebox.showwarning("Campo incompleto", "Por favor completa tu nombre y correo electrónico.")
                return

            datos = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "nombre": nombre,
                "email": email,
                "emocion": self.preg1_var.get(),
                "intensidad": self.preg2_var.get(),
                "comentario": self.preg3_var.get().strip()
            }

            # Intentar guardar en la ruta data_path, con DATA_DIR como respaldo
            csv_path = os.path.join(self.data_path, "respuestas_encuesta.csv")
            encabezados = ["timestamp", "nombre", "email", "emocion", "intensidad", "comentario"]

            # Verificar si podemos escribir en data_path
            try:
                # Crear directorio si no existe
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                
                nuevo = not os.path.exists(csv_path)
                
                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=encabezados)
                    if nuevo:
                        writer.writeheader()
                    writer.writerow(datos)
                logger.info(f"Encuesta guardada correctamente para {nombre} en {csv_path}")
            except Exception as e:
                logger.error(f"Error al guardar encuesta en {csv_path}: {str(e)}")
                
                # Intentar con DATA_DIR como alternativa si es diferente
                if self.data_path != DATA_DIR:
                    try:
                        alt_csv_path = os.path.join(DATA_DIR, "respuestas_encuesta.csv")
                        os.makedirs(os.path.dirname(alt_csv_path), exist_ok=True)
                        
                        alt_nuevo = not os.path.exists(alt_csv_path)
                        
                        with open(alt_csv_path, "a", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=encabezados)
                            if alt_nuevo:
                                writer.writeheader()
                            writer.writerow(datos)
                        logger.info(f"Encuesta guardada en ruta alternativa {alt_csv_path}")
                        csv_path = alt_csv_path  # Actualizar ruta para mensaje de éxito
                    except Exception as e2:
                        logger.error(f"Error al guardar encuesta en ruta alternativa {alt_csv_path}: {str(e2)}")
                        messagebox.showerror("Error", f"No se pudo guardar la encuesta en ninguna ubicación:\n{str(e2)}")
                        return
                else:
                    messagebox.showerror("Error", f"No se pudo guardar la encuesta:\n{str(e)}")
                    return

            messagebox.showinfo("Gracias", "Tus respuestas han sido registradas exitosamente.")
            self.name_var.set("")
            self.email_var.set("")
            self.preg1_var.set("neutral")
            self.preg2_var.set(5)
            self.preg3_var.set("")
            self.on_submit()
            
        except Exception as e:
            logger.error(f"Error al procesar encuesta: {str(e)}")
            messagebox.showerror("Error", f"Error al procesar encuesta: {str(e)}")