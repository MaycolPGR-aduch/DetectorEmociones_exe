def ejecutar_deepface():
    import cv2
    from deepface import DeepFace
    import os
    import numpy as np


    emoji_path = "img"
    emojis = {
        "angry": "angry.png",
        "disgust": "disgust.png",
        "fear": "fear.png",
        "happy": "happy.png",
        "sad": "sad.png",
        "surprise": "surprise.png",
        "neutral": "neutral.png"
    }

    emoji_imgs = {}
    for emotion, filename in emojis.items():
        path = os.path.join(emoji_path, filename)
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            emoji_imgs[emotion] = img

    cap = cv2.VideoCapture(0)
    print("[INFO] Presiona 'q' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        try:
            result = DeepFace.analyze(frame, actions=['emotion'], enforce_detection=False)[0]
            emotion = result['dominant_emotion']
            x, y, w, h = result['region']['x'], result['region']['y'], result['region']['w'], result['region']['h']

            # Dibuja rostro
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

            # Crear barra lateral negra 
            sidebar_width = 150
            black_bar = np.zeros((frame.shape[0], sidebar_width, 3), dtype=np.uint8)

            # Si hay emoji disponible, mostrarlo en la barra
            if emotion in emoji_imgs:
                emoji = emoji_imgs[emotion]
                emoji_resized = cv2.resize(emoji, (100, 100))

                if emoji_resized.shape[2] == 4:
                    for c in range(3):
                        alpha = emoji_resized[:, :, 3] / 255.0
                        black_bar[20:120, 25:125, c] = (
                            alpha * emoji_resized[:, :, c] +
                            (1 - alpha) * black_bar[20:120, 25:125, c]
                        )
                else:
                    black_bar[20:120, 25:125] = emoji_resized

            # Concatenar frame original + barra negra
            final_frame = np.hstack((frame, black_bar))
            cv2.imshow("DeepFace Emotions con Barra Lateral", final_frame)

        except Exception as e:
            print("Error:", e)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
