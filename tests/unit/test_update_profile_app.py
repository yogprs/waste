from unittest.mock import patch, MagicMock

PETUGAS_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"

# =========================
# TEST: data kosong
# =========================
def test_update_profile_no_data(client):
    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Data profile tidak ditemukan"


# =========================
# TEST: user_type tidak valid
# =========================
def test_update_profile_invalid_user_type(client):
    response = client.patch(f"/api/profile/guest/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Jenis akun tidak valid"


# =========================
# TEST: id_user bukan UUID
# =========================
def test_update_profile_invalid_uuid(client):
    response = client.patch("/api/profile/petugas/invalid-uuid", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format ID User tidak valid"


# =========================
# TEST: user tidak ditemukan di database
# =========================
@patch("app.supabase")
def test_update_profile_user_not_found(mock_supabase, client):
    mock_user = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com"
        }
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "User tidak ditemukan"


# =========================
# TEST: name kosong
# =========================
@patch("app.supabase")
def test_update_profile_name_empty(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Test"}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "",
            "email": "test@mail.com",
            "password": "password123"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Nama wajib diisi!"


# =========================
# TEST: email kosong
# =========================
@patch("app.supabase")
def test_update_profile_email_empty(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Test"}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "",
            "password": "password123"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email wajib diisi!"


# =========================
# TEST: password terlalu pendek
# =========================
@patch("app.supabase")
def test_update_profile_password_short(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Test"}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com",
            "password": "123"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password minimal 8 karakter"


# =========================
# TEST: validasi gagal (validateUsersData)
# =========================
@patch("app.validateUsersData")
@patch("app.supabase")
def test_update_profile_validation_error(mock_supabase, mock_validate, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Test"}])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_validate.return_value = "Format email tidak valid"

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "invalid-email",
            "password": "password123"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format email tidak valid"


# =========================
# TEST: email sudah digunakan akun lain
# =========================
@patch("app.supabase")
def test_update_profile_email_already_used(mock_supabase, client):
    current_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "old@mail.com", "nama": "Old Name"}])
    existing_email = MagicMock(data=[{"id_petugas": "other-uuid"}])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        current_user,
        existing_email
    ]

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "Updated Name",
            "email": "used@mail.com"
        }
    })

    assert response.status_code == 409
    assert response.get_json()["error"] == "Email sudah digunakan"


# =========================
# TEST: update sukses (tanpa password)
# =========================
@patch("app.supabase")
def test_update_profile_success_no_password(mock_supabase, client):
    current_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Old Name"}])
    mock_update_res = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "nama": "New Name", "email": "test@mail.com"}])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = current_user
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_res

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "New Name",
            "email": "test@mail.com"
        }
    })

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Profile berhasil diperbarui"
    assert data["data"]["name"] == "New Name"
    assert data["data"]["email"] == "test@mail.com"
    assert data["data"]["user_type"] == "petugas"


# =========================
# TEST: update sukses (dengan password)
# =========================
@patch("app.bcrypt.hashpw")
@patch("app.supabase")
def test_update_profile_with_password(mock_supabase, mock_hashpw, client):
    mock_hashpw.return_value = b"newhashedpw"

    current_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "email": "test@mail.com", "nama": "Old Name"}])
    mock_update_res = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "nama": "New Name", "email": "test@mail.com"}])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = current_user
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_update_res

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "New Name",
            "email": "test@mail.com",
            "password": "newpassword123"
        }
    })

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Profile berhasil diperbarui"
    assert data["data"]["name"] == "New Name"


# =========================
# TEST: update profile exception
# =========================
@patch("app.supabase")
def test_update_profile_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.patch(f"/api/profile/petugas/{PETUGAS_UUID}", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com"
        }
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan server"
