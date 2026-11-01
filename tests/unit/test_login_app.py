from unittest.mock import patch, MagicMock

# =========================
# TEST: email kosong
# =========================
def test_login_email_empty(client):
    response = client.post("/api/login", json={
        "email": "",
        "password": "12345678"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Email wajib diisi"


# =========================
# TEST: password kosong
# =========================
def test_login_password_empty(client):
    response = client.post("/api/login", json={
        "email": "test@mail.com",
        "password": ""
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password wajib diisi"


# =========================
# TEST: user tidak ditemukan (email tidak ditemukan)
# =========================
@patch("app.supabase")
def test_login_user_not_found(mock_supabase, client):
    mock_rpc_res = MagicMock()
    mock_rpc_res.data = None
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res

    response = client.post("/api/login", json={
        "email": "test@mail.com",
        "password": "12345678"
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Email tidak ditemukan"


# =========================
# TEST: password salah
# =========================
@patch("app.supabase")
@patch("app.bcrypt.checkpw")
def test_login_wrong_password(mock_checkpw, mock_supabase, client):
    mock_checkpw.return_value = False

    mock_rpc_res = MagicMock()
    mock_rpc_res.data = {
        "id": "1",
        "email": "test@mail.com",
        "name": "test",
        "password": "hashedpassword",
        "role": "petugas"
    }
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res

    response = client.post("/api/login", json={
        "email": "test@mail.com",
        "password": "wrongpassword"
    })

    assert response.status_code == 401
    assert response.get_json()["error"] == "Password salah"


# =========================
# TEST: login berhasil
# =========================
@patch("app.supabase")
@patch("app.bcrypt.checkpw")
def test_login_success(mock_checkpw, mock_supabase, client):
    mock_checkpw.return_value = True

    mock_rpc_res = MagicMock()
    mock_rpc_res.data = {
        "id": "1",
        "email": "test@mail.com",
        "name": "test",
        "password": "hashedpassword",
        "role": "admin"
    }
    mock_supabase.rpc.return_value.execute.return_value = mock_rpc_res

    response = client.post("/api/login", json={
        "email": "test@mail.com",
        "password": "12345678"
    })

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Login berhasil"
    assert data["user"]["email"] == "test@mail.com"
    assert data["user"]["role"] == "admin"


# =========================
# TEST: login server exception
# =========================
@patch("app.supabase")
def test_login_exception(mock_supabase, client):
    mock_supabase.rpc.side_effect = Exception("DB error")

    response = client.post("/api/login", json={
        "email": "test@mail.com",
        "password": "12345678"
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan pada server"
