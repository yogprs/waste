import base64
import numpy as np
from unittest.mock import patch, MagicMock
from app import socketio, app, uploaded_users

# =========================
# HELPER: fake base64 image
# =========================
def fake_base64_image():
    return "data:image/jpeg;base64," + base64.b64encode(b"fakeimage").decode()


# =========================
# HELPER: mock imencode (FIX UTAMA)
# =========================
def mock_imencode_success():
    return (True, np.frombuffer(b"fakeimage", dtype=np.uint8))


# =========================
# TEST: frame None
# =========================
@patch("app.cv2.imdecode")
def test_socket_frame_none(mock_imdecode):
    mock_imdecode.return_value = None

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()

    assert received == []


# =========================
# TEST: label None
# =========================
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
@patch("app.detect_trash")
def test_socket_label_none(mock_detect, mock_imdecode, mock_imencode):
    uploaded_users.clear()

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", None, None, None)
    mock_imencode.return_value = mock_imencode_success()

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()

    assert len(received) == 1

    data = received[0]["args"][0]

    assert data["label"] is None
    assert data["image_url"] is None
    assert data["type"] == "stream"


# =========================
# TEST: validasi label gagal
# =========================
@patch("app.validateHistoryData")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
@patch("app.detect_trash")
def test_socket_validation_label_failed(
    mock_detect, mock_imdecode, mock_imencode, mock_validate
):
    uploaded_users.clear()

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_imencode.return_value = mock_imencode_success()

    mock_validate.return_value = "Label tidak valid"

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]

    assert data["error"] == "Label tidak valid"
    assert data["image_url"] is None


# =========================
# TEST: validasi URL gagal
# =========================
@patch("app.validateHistoryData")
@patch("app.supabase")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
@patch("app.detect_trash")
def test_socket_validation_url_failed(
    mock_detect,
    mock_imdecode,
    mock_imencode,
    mock_supabase,
    mock_validate
):
    uploaded_users.clear()

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_imencode.return_value = mock_imencode_success()

    mock_validate.side_effect = [None, "URL tidak valid"]

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://img"

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]

    assert data["error"] == "URL tidak valid"
    assert data["image_url"] is None


# =========================
# TEST: sukses
# =========================
@patch("app.validateHistoryData")
@patch("app.supabase")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
@patch("app.detect_trash")
def test_socket_success(
    mock_detect,
    mock_imdecode,
    mock_imencode,
    mock_supabase,
    mock_validate
):
    uploaded_users.clear()

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_imencode.return_value = mock_imencode_success()

    mock_validate.return_value = None

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://img"

    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]

    assert data["label"] == "plastic"
    assert data["image_url"] == "http://img"
    assert data["type"] == "stream"


# =========================
# TEST: duplicate user
# =========================
@patch("app.validateHistoryData")
@patch("app.supabase")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
@patch("app.detect_trash")
def test_socket_duplicate_user(
    mock_detect,
    mock_imdecode,
    mock_imencode,
    mock_supabase,
    mock_validate
):
    uploaded_users.clear()

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_imencode.return_value = mock_imencode_success()

    mock_validate.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://img"

    client = socketio.test_client(app)

    # emit pertama
    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    # emit kedua
    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": "1"
    })

    received = client.get_received()
    assert len(received) >= 2

    data_second = received[-1]["args"][0]

    assert data_second["image_url"] is None