import base64
import numpy as np
from unittest.mock import patch, MagicMock
from app import socketio, app, uploaded_users

PETUGAS_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"

# =========================
# HELPER: fake base64 image
# =========================
def fake_base64_image():
    return "data:image/jpeg;base64," + base64.b64encode(b"fakeimage").decode()


# =========================
# HELPER: mock imencode
# =========================
def mock_imencode_success():
    return (True, np.frombuffer(b"fakeimage", dtype=np.uint8))


# =========================
# TEST: data input tidak lengkap
# =========================
def test_socket_missing_input():
    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": PETUGAS_UUID
        # missing user_type
    })

    received = client.get_received()
    assert len(received) == 1
    data = received[0]["args"][0]
    assert data["error"] == "Data gambar, user_id, dan user_type wajib diisi"


# =========================
# TEST: frame None (gagal decode)
# =========================
@patch("app.cv2.imdecode")
def test_socket_frame_none(mock_imdecode):
    mock_imdecode.return_value = None

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    received = client.get_received()
    assert len(received) == 1
    data = received[0]["args"][0]
    assert data["error"] == "Gambar tidak dapat diproses"


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
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
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
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]
    assert data["error"] == "Label tidak valid"


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
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]
    assert data["error"] == "URL tidak valid"


# =========================
# TEST: live scan sukses
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
    mock_detect.return_value = ("frame", "Organik", "Organik (95%)", "95%")
    mock_imencode.return_value = mock_imencode_success()
    mock_validate.return_value = None

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://img.jpg"

    # User existence check returns user
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    client = socketio.test_client(app)

    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    received = client.get_received()
    assert len(received) == 1

    data = received[0]["args"][0]
    assert data["label"] == "Organik"
    assert data["image_url"] == "http://img.jpg"
    assert data["type"] == "stream"


# =========================
# TEST: duplicate user (hanya stream, tidak re-upload)
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
    mock_detect.return_value = ("frame", "Organik", "Organik (95%)", "95%")
    mock_imencode.return_value = mock_imencode_success()
    mock_validate.return_value = None

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://img.jpg"

    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    client = socketio.test_client(app)

    # emit pertama (upload berhasil)
    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    # emit kedua (user_id sudah di uploaded_users, tidak re-upload)
    client.emit("image", {
        "image": fake_base64_image(),
        "user_id": PETUGAS_UUID,
        "user_type": "petugas"
    })

    received = client.get_received()
    assert len(received) == 2

    data_first = received[0]["args"][0]
    data_second = received[1]["args"][0]

    assert data_first["image_url"] == "http://img.jpg"
    assert data_second["image_url"] is None
    assert data_second["label"] == "Organik"
