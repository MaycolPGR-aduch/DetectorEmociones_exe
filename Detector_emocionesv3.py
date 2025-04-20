import cv2
from fer import FER
from datetime import datetime
import csv
import os

# Crear detector sin MTCNN para evitar errores con NumPy/Torch
detector = FER(mtcnn=False)

# Inicializar webcam
cap = cv2.VideoCapture(0)

# Crear archivo CSV si no existe
nombre_csv = 'emociones_log.csv'
if not os.path.exists(nombre_csv):
    with open(nombre_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['FechaHora', 'Emocion', 'Confianza (%)'])

print("[INFO] Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detectar emociones
    emociones = detector.detect_emotions(frame)

    for face in emociones:
        (x, y, w, h) = face["box"]
        emociones_detectadas = face["emotions"]

        # Emoción principal
        emocion_principal = max(emociones_detectadas, key=emociones_detectadas.get)
        confianza = emociones_detectadas[emocion_principal]

        # Solo mostrar si la confianza es mayor al 60%
        if confianza > 0.6:
            # Dibujar rostro y emoción
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            texto = f"{emocion_principal} ({int(confianza * 100)}%)"
            cv2.putText(frame, texto, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Guardar en CSV
            with open(nombre_csv, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                 emocion_principal,
                                 round(confianza * 100, 2)])

    cv2.imshow("Detector de emociones", frame)

    # Salir con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
