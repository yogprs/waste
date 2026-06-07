from unittest.mock import patch, MagicMock


# =========================
# TEST: JSON kosong
# =========================
def test_register_no_json(client):
    response = client.post("/api/register", json={})

    assert response.status_code == 400
    assert response.get_json()["error"] == "JSON tidak terbaca"


# =========================
# TEST: email kosong
# =========================
def test_register_email_empty(client):
    response = client.post("/api/register", json={
        "email": "",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email wajib diisi"


# =========================
# TEST: name kosong
# =========================
def test_register_name_empty(client):
    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Name wajib diisi"


# =========================
# TEST: password kosong
# =========================
def test_register_password_empty(client):
    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": ""
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password wajib diisi"


# =========================
# TEST: password kurang dari 8
# =========================
def test_register_password_short(client):
    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "123"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password minimal 8 karakter"


# =========================
# TEST: email sudah ada
# =========================
@patch("app.supabase")
def test_register_email_exists(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "1"}]  # user sudah ada

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email sudah terdaftar"


# =========================
# TEST: register sukses
# =========================
@patch("app.bcrypt.hashpw")
@patch("app.supabase")
def test_register_success(mock_supabase, mock_hashpw, client):
    # mock hash password
    mock_hashpw.return_value = b"hashedpassword"

    # mock check email (tidak ada)
    mock_check = MagicMock()
    mock_check.data = []

    # mock insert berhasil
    mock_insert = MagicMock()
    mock_insert.data = [{"id": "123"}]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_check
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert

    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 201
    assert response.get_json()["message"] == "Register berhasil"


# =========================
# TEST: gagal insert
# =========================
@patch("app.bcrypt.hashpw")
@patch("app.supabase")
def test_register_insert_failed(mock_supabase, mock_hashpw, client):
    mock_hashpw.return_value = b"hashedpassword"

    # email tidak ada
    mock_check = MagicMock()
    mock_check.data = []

    # insert gagal
    mock_insert = MagicMock()
    mock_insert.data = None

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_check
    mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert

    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Gagal register"

# =========================
# TEST: validasi gagal data user (panjang email)
# =========================
@patch("app.validateUsersData")
def test_register_validate_users_failed(mock_validate, client):
    mock_validate.return_value = "Email tidak boleh melebihi dari 50 karakter!"

    response = client.post("/api/register", json={
        "email": "a" * 60 + "@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email tidak boleh melebihi dari 50 karakter!"

# =========================
# TEST: validasi data user (panjang password)
# =========================
def test_register_password_too_long(client):
    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "a" * 25
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password tidak boleh melebihi dari 20 karakter!"

# =========================
# TEST: validasi data user (panjang name)
# =========================
def test_register_name_too_long(client):
    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "a" * 60,
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Nama pengguna tidak boleh melebihi dari 50 karakter!"

# =========================
# TEST: validasi data user (panjang email)
# =========================
def test_register_email_too_long(client):
    response = client.post("/api/register", json={
        "email": "a" * 60 + "@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email tidak boleh melebihi dari 50 karakter!"

# =========================
# TEST: error dari database (exception)
# =========================
@patch("app.supabase")
def test_register_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.post("/api/register", json={
        "email": "test@mail.com",
        "name": "test",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert "error" in response.get_json()