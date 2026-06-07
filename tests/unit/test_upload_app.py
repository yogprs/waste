import io
from unittest.mock import patch, MagicMock

# =========================
# TEST: label tidak terdeteksi
# =========================
@patch("app.detect_trash")
@patch("app.cv2.imdecode")
def test_upload_no_detection(mock_imdecode, mock_detect, client):
    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", None, None, None)

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg")
    }

    response = client.post(
        "/api/upload/1",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 200
    assert "error" in response.get_json()

# =========================
# TEST: validasi label gagal
# =========================
@patch("app.validateHistoryData")
@patch("app.detect_trash")
@patch("app.cv2.imdecode")
def test_upload_validation_label_failed(mock_imdecode, mock_detect, mock_validate, client):
    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_validate.return_value = "Label tidak valid"

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg")
    }

    response = client.post(
        "/api/upload/1",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Label tidak valid"

# =========================
# TEST: validasi image gagal (setelah upload)
# =========================
@patch("app.validateHistoryData")
@patch("app.supabase")
@patch("app.detect_trash")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
def test_upload_validation_image_failed(
    mock_imdecode,
    mock_imencode,
    mock_detect,
    mock_supabase,
    mock_validate,
    client
):
    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")

    mock_imencode.return_value = (True, MagicMock(tobytes=lambda: b"image"))

    # validasi pertama lolos, kedua gagal
    mock_validate.side_effect = [None, "Image tidak valid"]

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://image.url"

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg")
    }

    response = client.post(
        "/api/upload/1",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Image tidak valid"

# =========================
# TEST: upload sukses
# =========================
@patch("app.validateHistoryData")
@patch("app.supabase")
@patch("app.detect_trash")
@patch("app.cv2.imencode")
@patch("app.cv2.imdecode")
def test_upload_success(
    mock_imdecode,
    mock_imencode,
    mock_detect,
    mock_supabase,
    mock_validate,
    client
):
    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")

    mock_imencode.return_value = (True, MagicMock(tobytes=lambda: b"image"))

    # semua validasi lolos
    mock_validate.return_value = None

    # mock storage
    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://image.url"

    # mock insert DB
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg")
    }

    response = client.post(
        "/api/upload/1",
        data=data,
        content_type="multipart/form-data"
    )

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["message"] == "Successfully"
    assert res_json["label"] == "plastic"
    assert res_json["image_url"] == "http://image.url"

