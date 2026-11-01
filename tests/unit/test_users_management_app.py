from unittest.mock import patch, MagicMock

ADMIN_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"
PETUGAS_UUID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
NASABAH_UUID = "f1e2d3c4-b5a6-4987-9876-543210fedcba"

# =========================
# TEST: get all users missing id_admin
# =========================
def test_get_all_users_missing_admin(client):
    response = client.get("/api/users")

    assert response.status_code == 400
    assert response.get_json()["error"] == "id_admin wajib diisi"


# =========================
# TEST: get all users invalid id_admin UUID
# =========================
def test_get_all_users_invalid_uuid(client):
    response = client.get("/api/users?id_admin=invalid-uuid")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format ID Admin tidak valid"


# =========================
# TEST: get all users access denied (bukan admin)
# =========================
@patch("app.supabase")
def test_get_all_users_access_denied(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_empty

    response = client.get(f"/api/users?id_admin={ADMIN_UUID}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Akses ditolak"


# =========================
# TEST: get all users success
# =========================
@patch("app.supabase")
def test_get_all_users_success(mock_supabase, client):
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_petugas_res = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "nama": "Budi", "email": "budi@mail.com"}])
    mock_nasabah_res = MagicMock(data=[{"id_nasabah": NASABAH_UUID, "nama": "Andi", "email": "andi@mail.com"}])

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_admin
        elif table_name == "petugas":
            mock_t.select.return_value.order.return_value.execute.return_value = mock_petugas_res
        elif table_name == "nasabah":
            mock_t.select.return_value.order.return_value.execute.return_value = mock_nasabah_res
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.get(f"/api/users?id_admin={ADMIN_UUID}")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total"] == 2
    assert len(res_json["data"]) == 2
    assert res_json["data"][0]["nama"] == "Andi"  # sorted by name
    assert res_json["data"][1]["nama"] == "Budi"


# =========================
# TEST: delete user role invalid
# =========================
def test_delete_user_invalid_role(client):
    response = client.delete(f"/api/users/admin/{PETUGAS_UUID}", json={
        "id_admin": ADMIN_UUID
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Tidak dapat menghapus akun dengan role ini"


# =========================
# TEST: delete user user not found
# =========================
@patch("app.supabase")
def test_delete_user_not_found(mock_supabase, client):
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_empty = MagicMock(data=[])

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_admin
        elif table_name == "petugas":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_empty
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.delete(f"/api/users/petugas/{PETUGAS_UUID}", json={
        "id_admin": ADMIN_UUID
    })

    assert response.status_code == 404
    assert response.get_json()["error"] == "Pengguna tidak ditemukan"


# =========================
# TEST: delete user success
# =========================
@patch("app.supabase")
def test_delete_user_success(mock_supabase, client):
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_admin
        elif table_name == "petugas":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
            mock_t.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.delete(f"/api/users/petugas/{PETUGAS_UUID}", json={
        "id_admin": ADMIN_UUID
    })

    assert response.status_code == 200
    assert response.get_json()["message"] == "Pengguna berhasil dihapus"


# =========================
# TEST: update password password too short
# =========================
def test_update_user_password_short(client):
    response = client.patch(f"/api/users/petugas/{PETUGAS_UUID}/password", json={
        "id_admin": ADMIN_UUID,
        "new_password": "123"
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Password minimal 8 karakter"


# =========================
# TEST: update password success
# =========================
@patch("app.bcrypt.hashpw")
@patch("app.supabase")
def test_update_user_password_success(mock_supabase, mock_hashpw, client):
    mock_hashpw.return_value = b"newhashed"
    mock_admin = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_admin
        elif table_name == "petugas":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
            mock_t.update.return_value.eq.return_value.execute.return_value = MagicMock()
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.patch(f"/api/users/petugas/{PETUGAS_UUID}/password", json={
        "id_admin": ADMIN_UUID,
        "new_password": "newpassword123"
    })

    assert response.status_code == 200
    assert response.get_json()["message"] == "Password berhasil diperbarui"
