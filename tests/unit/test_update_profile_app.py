from unittest.mock import patch, MagicMock

# =========================
# TEST: data kosong
# =========================
def test_update_profile_no_data(client):
    response = client.patch("/api/profile/1", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Data tidak ditemukan"

# =========================
# TEST: name kosong
# =========================
def test_update_profile_name_empty(client):
    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "",
            "email": "test@mail.com",
            "password": "12345678"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Nama wajib di isi!"    

# =========================
# TEST: email kosong
# =========================
def test_update_profile_email_empty(client):
    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "",
            "password": "12345678"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email wajib di isi!"

# =========================
# TEST: password terlalu pendek
# =========================
def test_update_profile_password_short(client):
    response = client.patch("/api/profile/1", json={
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
def test_update_profile_validation_error(mock_validate, client):
    mock_validate.return_value = "Email tidak valid"

    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "invalid",
            "password": "12345678"
        }
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email tidak valid"

# =========================
# TEST: user tidak ditemukan
# =========================
@patch("app.supabase")
def test_update_profile_user_not_found(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = None

    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com",
            "password": "12345678"
        }
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "User tidak ditemukan"

# =========================
# TEST: update sukses (tanpa password)
# =========================
@patch("app.supabase")
def test_update_profile_success_no_password(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{
        "id": "1",
        "name": "test",
        "email": "test@mail.com"
    }]

    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com",
            "password": ""
        }
    })

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Profile berhasil diperbarui"
    assert data["data"]["email"] == "test@mail.com"

# =========================
# TEST: update sukses (dengan password)
# =========================
@patch("app.bcrypt.hashpw")
@patch("app.supabase")
def test_update_profile_with_password(mock_supabase, mock_hashpw, client):
    mock_hashpw.return_value = b"hashedpassword"

    mock_response = MagicMock()
    mock_response.data = [{
        "id": "1",
        "name": "test",
        "email": "test@mail.com"
    }]

    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_response

    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com",
            "password": "12345678"
        }
    })

    assert response.status_code == 200
    assert response.get_json()["message"] == "Profile berhasil diperbarui"

# =========================
# TEST: exception (server error)
# =========================
@patch("app.supabase")
def test_update_profile_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.patch("/api/profile/1", json={
        "updatedUser": {
            "name": "test",
            "email": "test@mail.com",
            "password": "12345678"
        }
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan server"