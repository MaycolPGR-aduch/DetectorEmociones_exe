import os
import cv2
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import re
import time
import logging

# Importar config.py
from config import DATA_DIR, CASCADE_FILE

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("detector_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("registro")

class RegistroUsuario:
    def __init__(self, parent, data_path, volver_callback):
        self.parent = parent
        self.data_path = data_path
        # Verificar si la ruta data_path es consistente con DATA_DIR
        if data_path != DATA_DIR:
            logger.warning(f"Inconsistencia de rutas: data_path={data_path}, DATA_DIR={DATA_DIR}")
        
        self.volver_callback = volver_callback

        # Importar face_recognition usando nuestro wrapper
        try:
            from face_recognition_wrapper import get_face_recognition
            self.face_recognition = get_face_recognition(self.data_path)
            logger.info("Face recognition inicializado correctamente")
        except Exception as e:
            logger.error(f"Error al cargar face_recognition: {str(e)}")
            messagebox.showerror("Error", f"No se pudo cargar el módulo de reconocimiento facial: {str(e)}")
            self.face_recognition = None

        self.frame = None
        self.nombre_var = tk.StringVar()
        self.cap = None
        self.stop_flag = False
        self.video_label = None
        self.thread = None
        self.camera_active = False  # Flag para controlar si la cámara está activa

    def mostrar(self):
        if self.frame and self.frame.winfo_exists():
            self.frame.destroy()

        self.frame = tk.Frame(self.parent, bg="white")
        self.frame.pack(expand=True, fill="both")
        self.nombre_var.set("")
        self.stop_flag = False

        self._construir_gui()

        try:
            # Verificar si la cámara ya está en uso
            if self.camera_active:
                logger.warning("Se intentó iniciar la cámara cuando ya estaba activa")
                return

            # Intentar obtener la cámara con varios intentos
            for attempt in range(3):  # Intentar 3 veces
                try:
                    self.cap = cv2.VideoCapture(0)
                    if self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.camera_active = True
                        self._iniciar_video()
                        logger.info("Cámara inicializada correctamente")
                        break
                    else:
                        logger.warning(f"Intento {attempt+1}: La cámara no se pudo abrir")
                        if self.cap:
                            self.cap.release()
                            self.cap = None
                        time.sleep(1)  # Esperar antes de reintentar
                except Exception as e:
                    logger.error(f"Intento {attempt+1}: Error al inicializar cámara: {str(e)}")
                    if self.cap:
                        self.cap.release()
                        self.cap = None
                    time.sleep(1)  # Esperar antes de reintentar
            
            # Si después de todos los intentos no se pudo abrir
            if not self.camera_active:
                messagebox.showerror("Error", "No se pudo inicializar la cámara después de varios intentos.")
                logger.error("No se pudo inicializar la cámara después de varios intentos")
                
        except Exception as e:
            logger.error(f"Error al inicializar cámara: {str(e)}")
            messagebox.showerror("Error", f"No se pudo inicializar la cámara: {str(e)}")

    def ocultar(self):
        self.stop_flag = True
        # Liberar recursos con seguridad
        if self.cap:
            try:
                time.sleep(0.2)  # Dar tiempo para que el hilo de video termine
                self.cap.release()
                logger.info("Cámara liberada correctamente")
            except Exception as e:
                logger.error(f"Error al liberar cámara: {str(e)}")
            finally:
                self.cap = None
                self.camera_active = False
        
        if self.frame and self.frame.winfo_exists():
            self.frame.pack_forget()
        logger.info("Registro ocultado")

    def _volver(self):
        self.ocultar()
        self.volver_callback()

    def _construir_gui(self):
        tk.Label(self.frame, text="Registro de Usuario", font=("Segoe UI", 16, "bold"), bg="white")\
            .pack(pady=(15, 10))

        top = tk.Frame(self.frame, bg="white")
        top.pack(pady=10)

        tk.Label(top, text="Nombre completo:", bg="white").pack(side="left", padx=(0, 10))
        tk.Entry(top, textvariable=self.nombre_var, width=25).pack(side="left")

        ttk.Button(top, text="Guardar y Capturar", command=self._guardar_y_capturar)\
            .pack(side="left", padx=10)
        ttk.Button(top, text="Volver", command=self._volver).pack(side="left", padx=5)

        # Añadir un botón para reiniciar la cámara si hay problemas
        ttk.Button(top, text="Reiniciar Cámara", command=self._reiniciar_camara)\
            .pack(side="left", padx=5)

        self.video_label = tk.Label(self.frame, bg="black", width=640, height=480)
        self.video_label.pack(pady=20)
        
        # Añadir etiqueta de estado para la cámara
        self.cam_status = tk.StringVar(value="Estado: Iniciando cámara...")
        tk.Label(self.frame, textvariable=self.cam_status, fg="blue", bg="white").pack(pady=5)

    def _reiniciar_camara(self):
        """Función para reiniciar la cámara si hay problemas"""
        try:
            # Detener la cámara actual si existe
            self.stop_flag = True
            if self.cap:
                time.sleep(0.3)  # Esperar a que el hilo termine
                self.cap.release()
                self.cap = None
            
            self.camera_active = False
            self.cam_status.set("Estado: Reiniciando cámara...")
            
            # Esperar un momento antes de reiniciar
            time.sleep(1)
            
            # Reiniciar la cámara
            self.stop_flag = False
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.camera_active = True
                self._iniciar_video()
                self.cam_status.set("Estado: Cámara reiniciada correctamente")
                logger.info("Cámara reiniciada correctamente")
            else:
                self.cam_status.set("Estado: Error al reiniciar cámara")
                logger.error("No se pudo reiniciar la cámara")
                messagebox.showerror("Error", "No se pudo reiniciar la cámara.")
        except Exception as e:
            self.cam_status.set(f"Estado: Error - {str(e)}")
            logger.error(f"Error al reiniciar cámara: {str(e)}")
            messagebox.showerror("Error", f"Error al reiniciar cámara: {str(e)}")

    def _iniciar_video(self):
        def loop():
            error_count = 0
            max_errors = 10  # Límite de errores antes de detener
            frame_count = 0
            
            while not self.stop_flag and self.cap and self.cap.isOpened():
                try:
                    ret, frame = self.cap.read()
                    if not ret:
                        error_count += 1
                        logger.warning(f"Error leyendo frame de cámara ({error_count}/{max_errors})")
                        if error_count >= max_errors:
                            logger.error("Demasiados errores consecutivos de cámara")
                            self.cam_status.set("Estado: Error - Cámara no disponible")
                            # No cerrar automáticamente - dejar que el usuario use el botón de reinicio
                            break
                        time.sleep(0.1)
                        continue
                    
                    # Reiniciar contador de errores si leímos con éxito
                    error_count = 0
                    frame_count += 1
                    
                    # Actualizar mensaje de estado periódicamente
                    if frame_count % 30 == 0:  # Aproximadamente cada segundo
                        self.cam_status.set("Estado: Cámara funcionando correctamente")
                    
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil = Image.fromarray(rgb).resize((640, 480))
                    tk_img = ImageTk.PhotoImage(pil)

                    if self.video_label and self.video_label.winfo_exists():
                        self.video_label.imgtk = tk_img
                        self.video_label.configure(image=tk_img)
                    
                    time.sleep(0.03)  # ~30 FPS
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error en loop de video: {str(e)}")
                    if error_count >= max_errors:
                        logger.error("Demasiados errores en loop de video")
                        self.cam_status.set(f"Estado: Error - {str(e)}")
                        break
                    time.sleep(0.1)
            
            # Cuando termina el loop, liberar recursos
            if self.cap:
                try:
                    self.cap.release()
                    self.cap = None
                    self.camera_active = False
                    logger.info("Cámara liberada al finalizar loop de video")
                except Exception as e:
                    logger.error(f"Error liberando cámara al finalizar loop: {str(e)}")

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()
        logger.info("Thread de video iniciado")

    def _guardar_y_capturar(self):
        try:
            nombre = self.nombre_var.get().strip()
            if not nombre or not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚüÜñÑ ]+$', nombre):
                messagebox.showerror("Error", "Por favor ingresa un nombre válido sin caracteres especiales.")
                return

            if not self.cap or not self.cap.isOpened():
                messagebox.showerror("Error", "La cámara no está disponible. Intenta reiniciarla.")
                return

            if self.face_recognition is None:
                messagebox.showerror("Error", "El módulo de reconocimiento facial no está disponible.")
                return

            # Intentar guardar en la ruta data_path, con DATA_DIR como respaldo
            carpeta = os.path.join(self.data_path, "usuarios", nombre.replace(" ", "_"))
            
            # Verificar si la carpeta existe o se puede crear
            try:
                os.makedirs(carpeta, exist_ok=True)
                logger.info(f"Creando carpeta para usuario: {carpeta}")
            except Exception as e:
                logger.error(f"Error al crear carpeta en {carpeta}: {str(e)}")
                # Intentar usar DATA_DIR como respaldo
                carpeta_alt = os.path.join(DATA_DIR, "usuarios", nombre.replace(" ", "_"))
                if carpeta_alt != carpeta:
                    try:
                        os.makedirs(carpeta_alt, exist_ok=True)
                        logger.info(f"Creando carpeta alternativa para usuario: {carpeta_alt}")
                        carpeta = carpeta_alt
                    except Exception as e2:
                        logger.error(f"Error al crear carpeta alternativa: {str(e2)}")
                        messagebox.showerror("Error", "No se pudo crear la carpeta para guardar las fotos.")
                        return

            # Mostrar mensaje de progreso
            self.cam_status.set("Estado: Capturando fotos... Por favor, mira a la cámara")
            
            # Actualizar la interfaz para que se muestre el mensaje
            self.frame.update()
            
            fotos_guardadas = 0
            intentos = 0
            max_intentos = 40  # Aumentar el número de intentos

            while fotos_guardadas < 5 and intentos < max_intentos:
                if not self.cap or not self.cap.isOpened():
                    logger.error("Cámara cerrada durante la captura")
                    messagebox.showerror("Error", "La cámara se cerró durante la captura.")
                    return
                    
                ret, frame = self.cap.read()
                if not ret:
                    logger.warning(f"Error leyendo frame para captura (intento {intentos+1}/{max_intentos})")
                    intentos += 1
                    time.sleep(0.2)
                    continue

                # Actualizar la vista previa
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil = Image.fromarray(rgb).resize((640, 480))
                tk_img = ImageTk.PhotoImage(pil)
                if self.video_label and self.video_label.winfo_exists():
                    self.video_label.imgtk = tk_img
                    self.video_label.configure(image=tk_img)
                self.frame.update()  # Actualizar la interfaz
                
                try:
                    # Si estamos usando face_recognition fallback, usar OpenCV directamente
                    if hasattr(self.face_recognition, 'face_cascade'):
                        # Estamos usando el fallback
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        faces = self.face_recognition.face_cascade.detectMultiScale(gray, 1.1, 4)
                        has_faces = len(faces) > 0
                    else:
                        # Estamos usando face_recognition real
                        faces = self.face_recognition.face_locations(rgb)
                        has_faces = len(faces) > 0
                    
                    if has_faces:
                        # Actualizar mensaje
                        self.cam_status.set(f"Estado: Foto {fotos_guardadas+1}/5 capturada")
                        self.frame.update()
                        
                        ruta = os.path.join(carpeta, f"{fotos_guardadas}.jpg")
                        cv2.imwrite(ruta, frame)
                        logger.info(f"Guardada foto {fotos_guardadas+1}/5 en {ruta}")
                        fotos_guardadas += 1
                        
                        # Dibujar un recuadro verde para mostrar que se detectó la cara
                        if hasattr(self.face_recognition, 'face_cascade'):
                            # Fallback - faces ya tiene formato x,y,w,h
                            for (x, y, w, h) in faces:
                                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        else:
                            # Face_recognition real - convertir formato
                            for face in faces:
                                top, right, bottom, left = face
                                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        
                        # Mostrar frame con rectángulo
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        pil = Image.fromarray(rgb).resize((640, 480))
                        tk_img = ImageTk.PhotoImage(pil)
                        if self.video_label and self.video_label.winfo_exists():
                            self.video_label.imgtk = tk_img
                            self.video_label.configure(image=tk_img)
                        self.frame.update()
                        
                        time.sleep(0.8)  # Esperar más tiempo entre fotos
                except Exception as e:
                    logger.error(f"Error detectando rostros: {str(e)}")
                    
                intentos += 1
                # Pequeña pausa entre intentos
                time.sleep(0.1)

            # Actualizar interfaz con resultado
            if fotos_guardadas >= 5:
                self.cam_status.set("Estado: Usuario registrado correctamente")
                messagebox.showinfo("Registro exitoso", f"Usuario '{nombre}' registrado correctamente con {fotos_guardadas} fotos.")
                logger.info(f"Usuario '{nombre}' registrado exitosamente con {fotos_guardadas} fotos")
                self._volver()
            else:
                self.cam_status.set("Estado: No se detectó el rostro claramente")
                messagebox.showwarning("Falló", f"Se guardaron {fotos_guardadas}/5 fotos. No se detectó el rostro claramente. Intenta de nuevo.")
                logger.warning(f"Fallo al registrar usuario: solo se detectaron {fotos_guardadas} rostros de 5 requeridos")
        
        except Exception as e:
            logger.error(f"Error en guardar_y_capturar: {str(e)}")
            self.cam_status.set(f"Estado: Error - {str(e)}")
            messagebox.showerror("Error", f"Ocurrió un error al capturar: {str(e)}")



