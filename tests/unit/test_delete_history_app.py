from unittest.mock import patch, MagicMock

ADMIN_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"
ID_H1 = "11111111-1111-1111-1111-111111111111"
ID_H2 = "22222222-2222-2222-2222-222222222222"

# =========================
# TEST: user_type tidak valid
# =========================
def test_delete_history_invalid_user_type(client):
    response = client.delete("/api/history", json={
        "user_type": "guest",
        "id_user": ADMIN_UUID,
        "ids": [ID_H1],
        "delete_all": False
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Jenis akun tidak valid"


# =========================
# TEST: id_user kosong
# =========================
def test_delete_history_empty_user_id(client):
    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": "",
        "ids": [ID_H1],
        "delete_all": False
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "id_user wajib diisi"


# =========================
# TEST: delete selected tanpa ids
# =========================
def test_delete_selected_no_ids(client):
    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": [],
        "delete_all": False
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "IDs wajib diisi untuk menghapus riwayat terpilih"


# =========================
# TEST: ID riwayat bukan UUID
# =========================
def test_delete_selected_invalid_uuid(client):
    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": ["invalid-uuid"],
        "delete_all": False
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "Terdapat ID riwayat yang tidak valid"


# =========================
# TEST: user tidak ada di database
# =========================
@patch("app.supabase")
def test_delete_history_user_not_found(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_empty

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": [ID_H1],
        "delete_all": False
    })

    assert response.status_code == 403
    assert response.get_json()["error"] == "Akun tidak ditemukan atau tidak memiliki akses"


# =========================
# TEST: delete selected success
# =========================
@patch("app.supabase")
def test_delete_selected_success(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_records = MagicMock(data=[
        {"id_riwayat": ID_H1, "gambar": "http://supabase.co/storage/v1/object/public/images/a.jpg"},
        {"id_riwayat": ID_H2, "gambar": "http://supabase.co/storage/v1/object/public/images/b.jpg"},
    ])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_records
    mock_supabase.table.return_value.delete.return_value.in_.return_value.execute.return_value = MagicMock()
    mock_supabase.storage.from_.return_value.remove.return_value = None

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": [ID_H1, ID_H2],
        "delete_all": False
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["mode"] == "selected"
    assert res_json["deleted_count"] == 2
    assert "a.jpg" in res_json["deleted_files"]
    assert "b.jpg" in res_json["deleted_files"]


# =========================
# TEST: delete all success
# =========================
@patch("app.supabase")
def test_delete_all_success(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_records = MagicMock(data=[
        {"id_riwayat": ID_H1, "gambar": "http://supabase.co/storage/v1/object/public/images/a.jpg"}
    ])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.select.return_value.execute.return_value = mock_records
    mock_supabase.table.return_value.delete.return_value.in_.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "delete_all": True
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["mode"] == "all"
    assert res_json["deleted_count"] == 1
    assert "a.jpg" in res_json["deleted_files"]


# =========================
# TEST: delete all dengan filter label
# =========================
@patch("app.supabase")
def test_delete_all_with_label(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_records = MagicMock(data=[
        {"id_riwayat": ID_H1, "gambar": "http://supabase.co/storage/v1/object/public/images/a.jpg"}
    ])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_records
    mock_supabase.table.return_value.delete.return_value.in_.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "delete_all": True,
        "label": "Organik"
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["mode"] == "all"
    assert res_json["deleted_count"] == 1


# =========================
# TEST: tidak ada riwayat yang cocok
# =========================
@patch("app.supabase")
def test_delete_no_records_found(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_empty = MagicMock(data=[])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_empty

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": [ID_H1],
        "delete_all": False
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["deleted_count"] == 0
    assert res_json["message"] == "Tidak ada riwayat yang dapat dihapus"


# =========================
# TEST: delete history exception
# =========================
@patch("app.supabase")
def test_delete_history_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.delete("/api/history", json={
        "user_type": "admin",
        "id_user": ADMIN_UUID,
        "ids": [ID_H1],
        "delete_all": False
    })

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan saat menghapus riwayat"
