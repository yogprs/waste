import cv2
import numpy as np
import tensorflow as tf
import json
from collections import deque

# ======================
# LOAD MODEL
# ======================
model_cls = tf.keras.models.load_model("best_model.h5")

with open("class_indices.json") as f:
    class_indices = json.load(f)

CLASS_NAMES = list(class_indices.keys())

IMG_SIZE = 224
CONF_THRESHOLD = 0.7

# ======================
# FACE DETECTOR
# ======================
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)

# ======================
# SMOOTHING HISTORY
# ======================
history = deque(maxlen=5)


def detect_trash(frame):
    global history

    h, w, _ = frame.shape

    # ======================
    # BOUNDING BOX TENGAH
    # ======================
    x1 = int(w * 0.15)
    y1 = int(h * 0.15)
    x2 = int(w * 0.85)
    y2 = int(h * 0.85)

    crop = frame[y1:y2, x1:x2]

    # ======================
    # DETEKSI WAJAH
    # ======================
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    skip = False

    for (fx, fy, fw, fh) in faces:
        padding = int(fh * 0.8)

        fx1 = fx - padding
        fy1 = fy - padding
        fx2 = fx + fw + padding
        fy2 = fy + fh + padding

        if (fx1 < x2 and fx2 > x1 and fy1 < y2 and fy2 > y1):
            skip = True
            break

    # ======================
    # CEK BLUR
    # ======================
    blur = cv2.Laplacian(crop, cv2.CV_64F).var()

    # ======================
    # DETEKSI KULIT
    # ======================
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    lower_skin = np.array([0, 30, 60])
    upper_skin = np.array([20, 150, 255])

    skin_mask = cv2.inRange(hsv, lower_skin, upper_skin)
    skin_ratio = np.sum(skin_mask > 0) / (crop.shape[0] * crop.shape[1])

    label = None
    label_with_accuracy = None
    accuracy = None

    # ======================
    # FILTER GLOBAL
    # ======================
    if blur < 50 or skip or skin_ratio > 0.3:

        # RESET HISTORY
        history.clear()

        color = (255,255,255)

    else:
        # ======================
        # PREPROCESS CNN
        # ======================
        img = cv2.resize(crop, (IMG_SIZE, IMG_SIZE))
        img = img / 255.0
        img = np.expand_dims(img, axis=0)

        pred = model_cls.predict(img, verbose=0)[0]

        history.append(pred)

        if len(history) >= 3:
            avg_pred = np.mean(history, axis=0)

            idx = np.argmax(avg_pred)
            conf = avg_pred[idx]

            if conf > CONF_THRESHOLD:
                label = CLASS_NAMES[idx]
                label_with_accuracy = f"{CLASS_NAMES[idx]} ({conf*100:.1f}%)"
                accuracy = f"{conf*100:.1f}%"
                color = (0,255,0)
            else:
                color = (255,255,255)
        else:
            color = (255,255,255)

    # ======================
    # DRAW
    # ======================
    cv2.rectangle(frame, (x1,y1), (x2,y2), color, 2)

    if label_with_accuracy:
        cv2.putText(frame, label_with_accuracy, (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

    print(label)
    return frame, label, label_with_accuracy, accuracy