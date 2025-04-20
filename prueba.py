import face_recognition
import cv2
import numpy as np

# Captura video desde la webcam
video_capture = cv2.VideoCapture(0)

while True:
    # Captura un solo frame de video
    ret, frame = video_capture.read()
    
    # Convierte la imagen de BGR a RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    
    # Encuentra todas las caras en el frame
    face_locations = face_recognition.face_locations(rgb_frame)
    
    # Muestra cuántas caras se encontraron
    if face_locations:
        print(f"Encontré {len(face_locations)} rostro(s)")
    
    # Dibuja un rectángulo alrededor de cada rostro
    for (top, right, bottom, left) in face_locations:
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
    
    # Muestra el resultado
    cv2.imshow('Video', frame)
    
    # Presiona 'q' para salir
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera la cámara y cierra las ventanas
video_capture.release()
cv2.destroyAllWindows()