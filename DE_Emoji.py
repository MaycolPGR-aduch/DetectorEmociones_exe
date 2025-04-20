def ejecutar_fer():
    import cv2
    from fer import FER
    import os

    # Inicializa el detector
    detector = FER(mtcnn=False)

    # Captura de la cámara
    cap = cv2.VideoCapture(0)

    # Ruta de los emojis
    emoji_path = "img"

    # Mapeo emoción → nombre de archivo de emoji
    emojis = {
        "angry": "angry.png",
        "disgust": "disgust.png",
        "fear": "fear.png",
        "happy": "happy.png",
        "sad": "sad.png",
        "surprise": "surprise.png",
        "neutral": "neutral.png"
    }

    # Cargar todos los emojis
    emoji_imgs = {}
    for emotion, filename in emojis.items():
        path = os.path.join(emoji_path, filename)
        emoji_img = cv2.imread(path, cv2.IMREAD_UNCHANGED)  # con canal alpha
        if emoji_img is not None:
            emoji_imgs[emotion] = emoji_img

    print("[INFO] Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        emociones = detector.detect_emotions(frame)

        for face in emociones:
            (x, y, w, h) = face["box"]
            emociones_detectadas = face["emotions"]
            emocion_principal = max(emociones_detectadas, key=emociones_detectadas.get)
            confianza = emociones_detectadas[emocion_principal]

            # Dibuja el recuadro del rostro
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Mostrar texto
            texto = f"{emocion_principal} ({int(confianza * 100)}%)"
            cv2.putText(frame, texto, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Mostrar emoji si existe
            if emocion_principal in emoji_imgs:
                emoji = emoji_imgs[emocion_principal]
                emoji_resized = cv2.resize(emoji, (w, h))

                # Calcular las coordenadas donde se colocará el emoji (a la derecha del rostro)
                x_emoji = x + w
                y_emoji = y

                # Evitar que el emoji se salga de los límites de la imagen
                if x_emoji + w > frame.shape[1]:
                    x_emoji = frame.shape[1] - w
                if y_emoji + h > frame.shape[0]:
                    y_emoji = frame.shape[0] - h

                # Si tiene canal alpha (transparencia)
                if emoji_resized.shape[2] == 4:
                    for c in range(3):
                        alpha = emoji_resized[:, :, 3] / 255.0
                        frame[y_emoji:y_emoji+h, x_emoji:x_emoji+w, c] = \
                            (alpha * emoji_resized[:, :, c] +
                            (1 - alpha) * frame[y_emoji:y_emoji+h, x_emoji:x_emoji+w, c])
                else:
                    frame[y_emoji:y_emoji+h, x_emoji:x_emoji+w] = emoji_resized

        cv2.imshow("Detector de emociones con emojis", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
