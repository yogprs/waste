import io
from unittest.mock import patch, MagicMock

PETUGAS_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"

# =========================
# TEST: role tidak valid
# =========================
def test_upload_invalid_role(client):
    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "invalid"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Role tidak valid"


# =========================
# TEST: file tidak diupload
# =========================
def test_upload_no_file(client):
    data = {
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "File wajib diupload"


# =========================
# TEST: user tidak ditemukan di database
# =========================
@patch("app.supabase")
def test_upload_user_not_found(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_empty

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "User tidak ditemukan"


# =========================
# TEST: label tidak terdeteksi
# =========================
@patch("app.supabase")
@patch("app.detect_trash")
@patch("app.cv2.imdecode")
def test_upload_no_detection(mock_imdecode, mock_detect, mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", None, None, None)

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert "tidak terdeteksi" in response.get_json()["error"]


# =========================
# TEST: validasi label gagal
# =========================
@patch("app.supabase")
@patch("app.validateHistoryData")
@patch("app.detect_trash")
@patch("app.cv2.imdecode")
def test_upload_validation_label_failed(
    mock_imdecode, mock_detect, mock_validate, mock_supabase, client
):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "plastic", "plastic (90%)", "90%")
    mock_validate.return_value = "Label tidak valid"

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 400
    assert response.get_json()["error"] == "Label tidak valid"


# =========================
# TEST: validasi image URL gagal (setelah upload ke storage)
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
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "Organik", "Organik (90%)", "90%")
    mock_imencode.return_value = (True, MagicMock(tobytes=lambda: b"image"))

    # validasi 1 (label): lolos, validasi 2 (image_url): gagal
    mock_validate.side_effect = [None, "Image tidak valid"]

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://image.url"
    mock_supabase.storage.from_.return_value.remove.return_value = None

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
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
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    mock_imdecode.return_value = "frame"
    mock_detect.return_value = ("frame", "Organik", "Organik (95%)", "95%")
    mock_imencode.return_value = (True, MagicMock(tobytes=lambda: b"image"))
    mock_validate.return_value = None

    mock_supabase.storage.from_.return_value.upload.return_value = None
    mock_supabase.storage.from_.return_value.get_public_url.return_value = "http://image.url"
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock()

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["message"] == "Upload berhasil"
    assert res_json["label"] == "Organik"
    assert res_json["image_url"] == "http://image.url"
    assert res_json["role"] == "petugas"


# =========================
# TEST: upload exception
# =========================
@patch("app.supabase")
@patch("app.cv2.imdecode")
def test_upload_exception(mock_imdecode, mock_supabase, client):
    mock_imdecode.side_effect = Exception("Crash")

    data = {
        "file": (io.BytesIO(b"fake image"), "test.jpg"),
        "role": "petugas"
    }

    response = client.post(
        f"/api/upload/{PETUGAS_UUID}",
        data=data,
        content_type="multipart/form-data"
    )

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan saat upload"
