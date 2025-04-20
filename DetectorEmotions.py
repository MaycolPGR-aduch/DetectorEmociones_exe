import face_recognition
import cv2
import numpy as np
import os
from datetime import datetime

class FaceEmotionRecognizer:
    def __init__(self, known_faces_dir="known_faces"):
        # Directorio para guardar rostros conocidos
        self.known_faces_dir = known_faces_dir
        
        # Crear directorio si no existe
        if not os.path.exists(known_faces_dir):
            os.makedirs(known_faces_dir)
        
        # Cargar caras conocidas
        self.known_face_encodings = []
        self.known_face_names = []
        self.load_known_faces()
        
        # Etiquetas de emociones
        self.emotions = ["Enojo", "Disgusto", "Miedo", "Felicidad", "Tristeza", "Sorpresa", "Neutral"]
        
        # Parámetros
        self.process_this_frame = True
        
    def load_known_faces(self):
        """Carga los rostros conocidos desde el directorio"""
        for filename in os.listdir(self.known_faces_dir):
            if filename.endswith(".jpg") or filename.endswith(".png"):
                name = os.path.splitext(filename)[0]
                image_path = os.path.join(self.known_faces_dir, filename)
                
                # Cargar imagen y encodear rostro
                face_img = face_recognition.load_image_file(image_path)
                face_encoding = face_recognition.face_encodings(face_img)
                
                if face_encoding:
                    self.known_face_encodings.append(face_encoding[0])
                    self.known_face_names.append(name)
                    print(f"Rostro cargado: {name}")
    
    def register_new_face(self, frame, name):
        """Registra un nuevo rostro"""
        # Detectar rostros en el frame
        face_locations = face_recognition.face_locations(frame)
        
        if not face_locations:
            return False, "No se detectó ningún rostro"
        
        if len(face_locations) > 1:
            return False, "Se detectaron múltiples rostros. Solo debe haber una persona"
        
        # Encodear el rostro
        face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
        
        # Guardar el rostro y agregarlo a la lista de conocidos
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}.jpg"
        filepath = os.path.join(self.known_faces_dir, filename)
        
        # Recortar y guardar solo la cara
        top, right, bottom, left = face_locations[0]
        face_img = frame[top:bottom, left:right]
        cv2.imwrite(filepath, face_img)
        
        # Agregar a la lista de rostros conocidos
        self.known_face_encodings.append(face_encoding)
        self.known_face_names.append(name)
        
        return True, f"Rostro de {name} registrado exitosamente"
    
    def analyze_emotion(self, face_img):
        """
        Analiza la emoción en un rostro
        (Nota: Esta es una implementación simplificada. Para un análisis más preciso,
        deberías usar un modelo pre-entrenado específico para emociones)
        """
        # Esta es una implementación simulada
        # Para un proyecto real, deberías integrar un modelo pre-entrenado
        # como FER (Facial Emotion Recognition) o utilizar una API como Microsoft Face API
        
        # Implementación simulada basada en características faciales simples
        # En un proyecto real, reemplazarías esto con un clasificador real
        
        # Aquí estamos generando una emoción aleatoria ponderada para demostración
        # En un proyecto real, usarías un modelo de ML para predecir la emoción
        
        # Detectar puntos faciales
        face_landmarks = face_recognition.face_landmarks(face_img)
        
        if not face_landmarks:
            return "Desconocido"
        
        # En un proyecto real aquí analizarías los landmarks para determinar la emoción
        # Por ahora devolvemos una básica basada en características simples
        landmarks = face_landmarks[0]
        
        # Simplificado: detectar sonrisa basada en la posición de los labios
        top_lip = landmarks.get('top_lip', [])
        bottom_lip = landmarks.get('bottom_lip', [])
        
        if top_lip and bottom_lip:
            # Calcular la altura promedio de la boca
            top_y = sum(point[1] for point in top_lip) / len(top_lip)
            bottom_y = sum(point[1] for point in bottom_lip) / len(bottom_lip)
            mouth_height = bottom_y - top_y
            
            # Detectar si está sonriendo (simplificado)
            if mouth_height > 10:
                return "Felicidad"
            else:
                return "Neutral"
        
        # Fallback a neutral si no podemos determinar
        return "Neutral"
    
    def run(self):
        """Ejecuta el reconocimiento facial y análisis de emociones en tiempo real"""
        # Activar la cámara
        video_capture = cv2.VideoCapture(0)
        
        if not video_capture.isOpened():
            print("No se pudo acceder a la cámara")
            return
        
        print("Presiona 'q' para salir")
        print("Presiona 'r' para registrar un nuevo rostro")
        
        registration_mode = False
        new_face_name = ""
        
        while True:
            # Capturar un frame de video
            ret, frame = video_capture.read()
            if not ret:
                break
                
            # Solo procesar cada segundo frame para ahorrar procesamiento
            if self.process_this_frame:
                # Redimensionar frame para acelerar el procesamiento
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                
                # Convertir de BGR (OpenCV) a RGB (face_recognition)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                # Encontrar todas las caras en el frame
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                face_emotions = []
                
                for face_encoding in face_encodings:
                    # Ver si la cara coincide con alguna conocida
                    name = "Desconocido"
                    if self.known_face_encodings:
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        
                        # Usar la cara conocida con menor distancia
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            if matches[best_match_index]:
                                name = self.known_face_names[best_match_index]
                    
                    face_names.append(name)
                    
                    # Analizar la emoción (en un frame real, no en el redimensionado)
                    # Si tenemos una cara, recortarla y pasar solo la región de la cara
                    emotion = "Analizando..."
                    face_emotions.append(emotion)
            
            self.process_this_frame = not self.process_this_frame
            
            # Mostrar los resultados
            for (top, right, bottom, left), name, emotion in zip(face_locations, face_names, face_emotions):
                # Escalar de vuelta las ubicaciones de caras ya que redimensionamos el frame
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Si estamos en el frame de procesamiento, analizar la emoción con la cara completa
                if self.process_this_frame:
                    face_img = frame[top:bottom, left:right]
                    emotion = self.analyze_emotion(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
                
                # Dibujar un rectángulo alrededor de la cara
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                
                # Mostrar nombre y emoción
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                cv2.putText(frame, f"{name}", (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
                
                # Mostrar emoción arriba del rectángulo
                cv2.putText(frame, f"Emoción: {emotion}", (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Si estamos en modo registro, mostrar instrucciones
            if registration_mode:
                cv2.putText(frame, "Modo de registro activado", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, f"Nombre: {new_face_name}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv2.putText(frame, "Presiona 'c' para capturar o 'esc' para cancelar", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Mostrar el frame resultante
            cv2.imshow('Reconocimiento Facial y Emociones', frame)
            
            # Capturar pulsación de tecla
            key = cv2.waitKey(1) & 0xFF
            
            # Si se presiona 'q', salir
            if key == ord('q'):
                break
            
            # Si se presiona 'r', activar modo de registro
            elif key == ord('r') and not registration_mode:
                registration_mode = True
                new_face_name = input("Ingresa el nombre de la persona: ")
            
            # Si se presiona 'c' en modo registro, capturar rostro
            elif key == ord('c') and registration_mode:
                success, message = self.register_new_face(frame, new_face_name)
                print(message)
                registration_mode = False
            
            # Si se presiona 'esc' en modo registro, cancelar
            elif key == 27 and registration_mode:  # 27 es el código ASCII para Esc
                print("Registro cancelado")
                registration_mode = False
        
        # Liberar recursos
        video_capture.release()
        cv2.destroyAllWindows()

# Para ejecutar el programa
if __name__ == "__main__":
    recognizer = FaceEmotionRecognizer()
    recognizer.run()