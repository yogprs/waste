import cv2
import numpy as np
import tensorflow as tf
import json
import h5py
import shutil
import os
from collections import deque


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "best_model.h5"
CLASS_INDEX_PATH = "class_indices.json"

IMG_SIZE = 224

# accuracy minimum
ACC_THRESHOLD = 0.70

# Jumlah frame untuk smoothing
HISTORY_LENGTH = 5

# Minimal jumlah prediction sebelum label ditampilkan
MIN_HISTORY = 3

# Blur threshold
BLUR_THRESHOLD = 50

# Skin ratio maksimum
SKIN_RATIO_THRESHOLD = 0.30

# Live ROI
LIVE_MARGIN = 0.15

# Upload ROI fallback
UPLOAD_MARGIN = 0.05


# ============================================================
# PREDICTION HISTORY
# ============================================================

prediction_histories = {}


def get_history(sid):
    if sid not in prediction_histories:
        prediction_histories[sid] = deque(maxlen=HISTORY_LENGTH)

    return prediction_histories[sid]


def clear_history(sid):
    prediction_histories.pop(sid, None)


def reset_prediction_history(sid):
    clear_history(sid)


# ============================================================
# COMPATIBILITY FIX
# ============================================================

def _remove_unsupported_keys(obj):
    """
    Recursively remove unsupported Keras configuration keys
    untuk kompatibilitas Keras 2 / Keras 3.
    """

    unsupported = {
        "quantization_config",
        "optional",
        "input_axes",
        "output_axes",
        "renorm",
        "renorm_clipping",
        "renorm_momentum"
    }

    if isinstance(obj, dict):

        # Keras 3 -> Keras 2 compatibility
        if "batch_shape" in obj and "batch_input_shape" not in obj:
            obj["batch_input_shape"] = obj.pop("batch_shape")

        for key in list(obj.keys()):

            if key in unsupported:
                del obj[key]

            else:
                _remove_unsupported_keys(obj[key])

    elif isinstance(obj, list):

        for item in obj:
            _remove_unsupported_keys(item)


def load_model_compat(model_path):

    try:

        print("[INFO] Loading model...")

        model = tf.keras.models.load_model(model_path)

        print("[INFO] Model loaded successfully.")

        return model

    except (TypeError, ValueError) as e:

        print(
            "[INFO] Standard model loading failed."
        )

        print(
            "[INFO] Applying compatibility fix..."
        )

        tmp_path = model_path + ".compat_tmp.h5"

        shutil.copy2(model_path, tmp_path)

        try:

            with h5py.File(tmp_path, "r+") as f:

                model_config = f.attrs.get("model_config")

                if model_config is None:
                    raise ValueError(
                        "model_config tidak ditemukan di file H5."
                    )

                if isinstance(model_config, bytes):
                    model_config = model_config.decode("utf-8")

                config = json.loads(model_config)

                _remove_unsupported_keys(config)

                f.attrs["model_config"] = json.dumps(config)

            model = tf.keras.models.load_model(tmp_path)

            print(
                "[INFO] Model loaded with compatibility fix."
            )

            return model

        finally:

            if os.path.exists(tmp_path):
                os.remove(tmp_path)


# ============================================================
# LOAD MODEL
# ============================================================

model_cls = load_model_compat(MODEL_PATH)


# ============================================================
# LOAD CLASS INDICES
# ============================================================

with open(CLASS_INDEX_PATH, "r") as f:
    class_indices = json.load(f)


# ============================================================
# SORT CLASS NAME BERDASARKAN INDEX
# ============================================================

CLASS_NAMES = [
    name
    for name, idx in sorted(
        class_indices.items(),
        key=lambda item: item[1]
    )
]


# ============================================================
# VALIDATE CLASS COUNT
# ============================================================

num_model_classes = model_cls.output_shape[-1]

num_class_names = len(CLASS_NAMES)


print(
    f"[INFO] Model output classes : {num_model_classes}"
)

print(
    f"[INFO] class_indices classes: {num_class_names}"
)

print(
    f"[INFO] CLASS_NAMES           : {CLASS_NAMES}"
)


if num_model_classes != num_class_names:

    raise ValueError(
        f"Class mismatch: model menghasilkan "
        f"{num_model_classes} kelas, tetapi "
        f"class_indices memiliki "
        f"{num_class_names} kelas."
    )


# ============================================================
# OPTIONAL: CHECK MODEL OUTPUT
# ============================================================

print(
    f"[INFO] Model input shape     : "
    f"{model_cls.input_shape}"
)

print(
    f"[INFO] Model output shape    : "
    f"{model_cls.output_shape}"
)


# ============================================================
# FACE DETECTOR
# ============================================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)


if face_cascade.empty():

    raise RuntimeError(
        "Haar Cascade face detector gagal dimuat."
    )


# ============================================================
# CREATE LIVE ROI
# ============================================================

def get_live_roi(frame):

    h, w = frame.shape[:2]

    x1 = int(w * LIVE_MARGIN)
    y1 = int(h * LIVE_MARGIN)

    x2 = int(w * (1.0 - LIVE_MARGIN))
    y2 = int(h * (1.0 - LIVE_MARGIN))

    return x1, y1, x2, y2


# ============================================================
# CREATE CENTER ROI (Untuk Tombol Scan Live)
# ============================================================

def get_center_roi(frame):

    h, w = frame.shape[:2]

    # Kotak persegi di tengah (50% dari lebar frame, aspect ratio 1:1 sesuai kotak panduan livescan)
    box_size = int(w * 0.5)

    if box_size > int(h * 0.8):
        box_size = int(h * 0.8)

    cx = w // 2
    cy = h // 2

    x1 = max(0, cx - box_size // 2)
    y1 = max(0, cy - box_size // 2)
    x2 = min(w, cx + box_size // 2)
    y2 = min(h, cy + box_size // 2)

    return x1, y1, x2, y2


# ============================================================
# CREATE UPLOAD ROI
# ============================================================

def get_upload_roi(frame):

    h, w = frame.shape[:2]

    # --------------------------------------------------------
    # Convert grayscale
    # --------------------------------------------------------

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Blur
    # --------------------------------------------------------

    gray_blur = cv2.GaussianBlur(
        gray,
        (5, 5),
        0
    )

    # --------------------------------------------------------
    # Edge detection
    # --------------------------------------------------------

    edges = cv2.Canny(
        gray_blur,
        50,
        150
    )

    # --------------------------------------------------------
    # Dilate
    # --------------------------------------------------------

    kernel = np.ones(
        (7, 7),
        np.uint8
    )

    dilated = cv2.dilate(
        edges,
        kernel,
        iterations=2
    )

    # --------------------------------------------------------
    # Find contours
    # --------------------------------------------------------

    contours, _ = cv2.findContours(
        dilated,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    # --------------------------------------------------------
    # Default fallback
    # --------------------------------------------------------

    default_x1 = int(w * UPLOAD_MARGIN)
    default_y1 = int(h * UPLOAD_MARGIN)

    default_x2 = int(w * (1.0 - UPLOAD_MARGIN))
    default_y2 = int(h * (1.0 - UPLOAD_MARGIN))

    if not contours:

        return (
            default_x1,
            default_y1,
            default_x2,
            default_y2
        )

    # --------------------------------------------------------
    # Filter contours
    # --------------------------------------------------------

    image_area = w * h

    valid_contours = []

    for contour in contours:

        area = cv2.contourArea(contour)

        if area < image_area * 0.02:
            continue

        if area > image_area * 0.90:
            continue

        valid_contours.append(
            contour
        )

    # --------------------------------------------------------
    # No valid contour
    # --------------------------------------------------------

    if not valid_contours:

        return (
            default_x1,
            default_y1,
            default_x2,
            default_y2
        )

    # --------------------------------------------------------
    # Select largest valid contour
    # --------------------------------------------------------

    contour = max(
        valid_contours,
        key=cv2.contourArea
    )

    cx, cy, cw, ch = cv2.boundingRect(
        contour
    )

    # --------------------------------------------------------
    # Padding
    # --------------------------------------------------------

    pad_x = int(cw * 0.20)
    pad_y = int(ch * 0.20)

    x1 = max(
        0,
        cx - pad_x
    )

    y1 = max(
        0,
        cy - pad_y
    )

    x2 = min(
        w,
        cx + cw + pad_x
    )

    y2 = min(
        h,
        cy + ch + pad_y
    )

    # --------------------------------------------------------
    # Check ROI size
    # --------------------------------------------------------

    roi_width = x2 - x1
    roi_height = y2 - y1

    if roi_width < w * 0.20:

        return (
            default_x1,
            default_y1,
            default_x2,
            default_y2
        )

    if roi_height < h * 0.20:

        return (
            default_x1,
            default_y1,
            default_x2,
            default_y2
        )

    return x1, y1, x2, y2


# ============================================================
# FACE DETECTION
# ============================================================

def detect_face_overlap(
    frame,
    x1,
    y1,
    x2,
    y2
):

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (
        fx,
        fy,
        fw,
        fh
    ) in faces:

        # Padding wajah
        padding = int(fh * 0.5)

        fx1 = max(
            0,
            fx - padding
        )

        fy1 = max(
            0,
            fy - padding
        )

        fx2 = min(
            frame.shape[1],
            fx + fw + padding
        )

        fy2 = min(
            frame.shape[0],
            fy + fh + padding
        )

        # Check intersection
        overlap = (
            fx1 < x2 and
            fx2 > x1 and
            fy1 < y2 and
            fy2 > y1
        )

        if overlap:
            return True

    return False


# ============================================================
# BLUR DETECTION
# ============================================================

def calculate_blur_score(crop):

    if crop is None:
        return 0.0

    if crop.size == 0:
        return 0.0

    gray = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2GRAY
    )

    score = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    return float(score)


# ============================================================
# SKIN DETECTION
# ============================================================

def calculate_skin_ratio(crop):

    if crop is None:
        return 1.0

    if crop.size == 0:
        return 1.0

    hsv = cv2.cvtColor(
        crop,
        cv2.COLOR_BGR2HSV
    )

    lower_skin = np.array(
        [0, 30, 60],
        dtype=np.uint8
    )

    upper_skin = np.array(
        [20, 150, 255],
        dtype=np.uint8
    )

    skin_mask = cv2.inRange(
        hsv,
        lower_skin,
        upper_skin
    )

    skin_pixels = np.sum(
        skin_mask > 0
    )

    total_pixels = (
        crop.shape[0] *
        crop.shape[1]
    )

    if total_pixels == 0:
        return 1.0

    return float(
        skin_pixels / total_pixels
    )


# ============================================================
# PREPROCESS IMAGE
# ============================================================

def preprocess_image(crop):

    if crop is None:
        return None

    if crop.size == 0:
        return None

    img = cv2.resize(
        crop,
        (IMG_SIZE, IMG_SIZE)
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Ini harus sama dengan preprocessing saat training.
    # --------------------------------------------------------

    img = img.astype(
        np.float32
    ) / 255.0

    img = np.expand_dims(
        img,
        axis=0
    )

    return img


# ============================================================
# CNN PREDICTION
# ============================================================

def predict_crop(crop):

    img = preprocess_image(
        crop
    )

    if img is None:
        return None

    pred = model_cls.predict(
        img,
        verbose=0
    )[0]

    pred = np.asarray(
        pred,
        dtype=np.float32
    )

    # --------------------------------------------------------
    # Validate output
    # --------------------------------------------------------

    if len(pred) != len(CLASS_NAMES):

        raise ValueError(
            f"Output model ({len(pred)}) "
            f"tidak sama dengan jumlah kelas "
            f"({len(CLASS_NAMES)})."
        )

    # --------------------------------------------------------
    # Jika output model bukan probability,
    # ubah menggunakan softmax.
    #
    # Jika model sudah menggunakan softmax,
    # bagian ini tidak mengubah hasil secara signifikan.
    # --------------------------------------------------------

    pred_sum = np.sum(pred)

    if (
        np.any(pred < 0)
        or
        np.any(pred > 1)
        or
        not np.isclose(
            pred_sum,
            1.0,
            atol=0.05
        )
    ):

        pred = tf.nn.softmax(
            pred
        ).numpy()

    return pred


# ============================================================
# MAIN DETECTION
# ============================================================

def detect_trash(
    frame,
    sid=None,
    is_upload=False,
    center_roi=False
):

    if frame is None:
        raise ValueError(
            "Frame tidak boleh None."
        )

    if frame.size == 0:
        raise ValueError(
            "Frame kosong."
        )

    # ========================================================
    # HISTORY
    # ========================================================

    history = None

    if not is_upload:

        if sid is None:

            raise ValueError(
                "sid is required for live detection"
            )

        history = get_history(
            sid
        )

    # ========================================================
    # FRAME SIZE
    # ========================================================

    h, w = frame.shape[:2]

    # ========================================================
    # GET ROI
    # ========================================================

    if center_roi:

        x1, y1, x2, y2 = get_center_roi(
            frame
        )

    elif is_upload:

        x1, y1, x2, y2 = get_upload_roi(
            frame
        )

    else:

        x1, y1, x2, y2 = get_live_roi(
            frame
        )

    # ========================================================
    # CROP
    # ========================================================

    crop = frame[
        y1:y2,
        x1:x2
    ]

    if crop.size == 0:

        return (
            frame,
            None,
            None,
            None
        )

    # ========================================================
    # FACE DETECTION
    # ========================================================

    face_detected = detect_face_overlap(
        frame,
        x1,
        y1,
        x2,
        y2
    )

    # ========================================================
    # BLUR
    # ========================================================

    blur_score = calculate_blur_score(
        crop
    )

    # ========================================================
    # SKIN
    # ========================================================

    skin_ratio = calculate_skin_ratio(
        crop
    )

    # ========================================================
    # DEFAULT RESULT
    # ========================================================

    label = None

    label_with_accuracy = None

    accuracy = None

    color = (
        255,
        255,
        255
    )

    # ========================================================
    # QUALITY FILTER
    # ========================================================

    invalid_quality = (
        blur_score < BLUR_THRESHOLD
        or
        face_detected
        or
        skin_ratio > SKIN_RATIO_THRESHOLD
    )

    # ========================================================
    # INVALID QUALITY
    # ========================================================

    if invalid_quality:

        # ----------------------------------------------------
        # Jangan langsung hapus history.
        #
        # Ini membuat live detection lebih stabil.
        # ----------------------------------------------------

        if not is_upload:

            # Jika history sudah terlalu lama,
            # baru dikurangi.
            if len(history) > 0:

                history.popleft()

        color = (
            255,
            255,
            255
        )

    # ========================================================
    # VALID QUALITY
    # ========================================================

    else:

        pred = predict_crop(
            crop
        )

        if pred is not None:

            # =================================================
            # UPLOAD
            # =================================================

            if is_upload:

                idx = int(
                    np.argmax(pred)
                )

                conf = float(
                    pred[idx]
                )

                if conf >= ACC_THRESHOLD:

                    label = CLASS_NAMES[idx]

                    accuracy = (
                        f"{conf * 100:.1f}%"
                    )

                    label_with_accuracy = (
                        f"{CLASS_NAMES[idx]} "
                        f"({conf * 100:.1f}%)"
                    )

                    color = (
                        0,
                        255,
                        0
                    )

                else:

                    color = (
                        255,
                        255,
                        255
                    )

            # =================================================
            # LIVE
            # =================================================

            else:

                history.append(
                    pred
                )

                # ------------------------------------------------
                # Tunggu minimal 3 frame
                # ------------------------------------------------

                if len(history) >= MIN_HISTORY:

                    avg_pred = np.mean(
                        np.array(history),
                        axis=0
                    )

                    idx = int(
                        np.argmax(avg_pred)
                    )

                    conf = float(
                        avg_pred[idx]
                    )

                    if conf >= ACC_THRESHOLD:

                        label = CLASS_NAMES[idx]

                        accuracy = (
                            f"{conf * 100:.1f}%"
                        )

                        label_with_accuracy = (
                            f"{CLASS_NAMES[idx]} "
                            f"({conf * 100:.1f}%)"
                        )

                        color = (
                            0,
                            255,
                            0
                        )

                    else:

                        color = (
                            255,
                            255,
                            255
                        )

                else:

                    color = (
                        255,
                        255,
                        255
                    )

    # ========================================================
    # DRAW ROI
    # ========================================================

    cv2.rectangle(
        frame,
        (x1, y1),
        (x2, y2),
        color,
        2
    )

    # ========================================================
    # DRAW LABEL
    # ========================================================

    if label_with_accuracy:

        text_y = y1 - 10

        # Jika terlalu dekat bagian atas
        if text_y < 25:
            text_y = y1 + 30

        cv2.putText(
            frame,
            label_with_accuracy,
            (x1, text_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            color,
            2
        )

    # ========================================================
    # RETURN
    # ========================================================

    return (
        frame,
        label,
        label_with_accuracy,
        accuracy
    )
