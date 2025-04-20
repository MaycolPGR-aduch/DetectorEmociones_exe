import cv2
from fer import FER



# Inicializa el detector con MTCNN para mejor precisión
detector = FER(mtcnn=False)

# Captura de la cámara (0 es la webcam principal)
cap = cv2.VideoCapture(0)

print("[INFO] Presiona 'q' para salir.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detecta emociones
    emociones = detector.detect_emotions(frame)

    for face in emociones:
        (x, y, w, h) = face["box"]
        emociones_detectadas = face["emotions"]

        # Determina la emoción principal
        emocion_principal = max(emociones_detectadas, key=emociones_detectadas.get)
        confianza = emociones_detectadas[emocion_principal]

        # Dibuja el recuadro del rostro y etiqueta con emoción
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        texto = f"{emocion_principal} ({int(confianza * 100)}%)"
        cv2.putText(frame, texto, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    cv2.imshow("Detector de emociones", frame)

    # Salida con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libera recursos
cap.release()
cv2.destroyAllWindows()
