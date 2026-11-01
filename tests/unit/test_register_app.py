from unittest.mock import patch, MagicMock

ADMIN_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"

# =========================
# TEST: JSON kosong
# =========================
def test_register_no_json(client):
    response = client.post("/api/create/user", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Data tidak boleh kosong"


# =========================
# TEST: email kosong
# =========================
def test_register_email_empty(client):
    response = client.post("/api/create/user", json={
        "email": "",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email wajib diisi"


# =========================
# TEST: name kosong
# =========================
def test_register_name_empty(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Name wajib diisi"


# =========================
# TEST: password kosong
# =========================
def test_register_password_empty(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password wajib diisi"


# =========================
# TEST: id_admin kosong
# =========================
def test_register_id_admin_empty(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": "",
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Id admin wajib ada"


# =========================
# TEST: role kosong
# =========================
def test_register_role_empty(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": ""
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Role User wajib diisi"


# =========================
# TEST: role tidak valid
# =========================
def test_register_role_invalid(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "invalid"
    })

    assert response.get_json()["error"] == "Role yang dipilih tidak valid"


# =========================
# TEST: id_admin bukan UUID
# =========================
def test_register_id_admin_invalid(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": "invalid-uuid",
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format ID Admin tidak valid"


# =========================
# TEST: password kurang dari 8
# =========================
def test_register_password_short(client):
    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password minimal 8 karakter"


# =========================
# TEST: validasi gagal (validateUsersData)
# =========================
@patch("app.validateUsersData")
def test_register_validate_users_failed(mock_validate, client):
    mock_validate.return_value = "Email tidak valid"

    response = client.post("/api/create/user", json={
        "email": "invalid",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email tidak valid"


# =========================
# TEST: email sudah terdaftar
# =========================
@patch("app.supabase")
def test_register_email_exists(mock_supabase, client):
    mock_exist = MagicMock()
    mock_exist.data = [{"email": "test@mail.com"}]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_exist

    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert "sudah terdaftar" in response.get_json()["error"]


# =========================
# TEST: admin tidak ditemukan (bukan akun admin)
# =========================
@patch("app.supabase")
def test_register_admin_not_found(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_empty

    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 403
    assert response.get_json()["error"] == "Akun yang anda gunakan tidak dapat melakukan aksi ini"


# =========================
# TEST: register sukses
# =========================
@patch("app.supabase")
def test_register_success(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_insert = MagicMock(data=[{"id_petugas": "generated-id"}])

    # Side effect for select: check_petugas -> empty, check_nasabah -> empty, check_admin -> admin found
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_empty,
        mock_empty,
        mock_admin
    ]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert

    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 201
    assert response.get_json()["message"] == "Berhasil membuat akun baru"


# =========================
# TEST: register gagal insert DB
# =========================
@patch("app.supabase")
def test_register_insert_failed(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_insert = MagicMock(data=None)

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_empty,
        mock_empty,
        mock_admin
    ]
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert

    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Gagal membuat akun baru"


# =========================
# TEST: register exception
# =========================
@patch("app.supabase")
def test_register_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.post("/api/create/user", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "password123",
        "id_admin": ADMIN_UUID,
        "role": "petugas"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "DB error"
