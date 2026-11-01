from unittest.mock import patch, MagicMock

ADMIN_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"
PETUGAS_UUID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"

# =========================
# TEST: jenis akun tidak valid
# =========================
def test_delete_profile_invalid_type(client):
    response = client.delete(f"/api/profile/guest/{PETUGAS_UUID}")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Jenis akun tidak valid"


# =========================
# TEST: akun admin tidak dapat dihapus
# =========================
def test_delete_profile_admin_forbidden(client):
    response = client.delete(f"/api/profile/admin/{ADMIN_UUID}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Akun admin tidak dapat dihapus"


# =========================
# TEST: format UUID tidak valid
# =========================
def test_delete_profile_invalid_uuid(client):
    response = client.delete("/api/profile/petugas/invalid-uuid")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format ID User tidak valid"


# =========================
# TEST: user tidak ditemukan di database
# =========================
@patch("app.supabase")
def test_delete_profile_user_not_found(mock_supabase, client):
    mock_user = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.delete(f"/api/profile/petugas/{PETUGAS_UUID}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "User tidak ditemukan"


# =========================
# TEST: delete profile success (dengan riwayat dan gambar)
# =========================
@patch("app.supabase")
def test_delete_profile_success(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_history = MagicMock(data=[
        {"id_riwayat": "h1", "gambar": "http://supabase.co/storage/v1/object/public/images/a.jpg"},
        {"id_riwayat": "h2", "gambar": "http://supabase.co/storage/v1/object/public/images/b.jpg"},
    ])
    mock_delete_history = MagicMock(data=[{"id_riwayat": "h1"}, {"id_riwayat": "h2"}])
    mock_delete_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])

    # 1st select: check user, 2nd select: get history
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,
        mock_history
    ]
    # 1st delete: delete history, 2nd delete: delete user
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.side_effect = [
        mock_delete_history,
        mock_delete_user
    ]
    mock_supabase.storage.from_.return_value.remove.return_value = None

    response = client.delete(f"/api/profile/petugas/{PETUGAS_UUID}")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total_history_deleted"] == 2
    assert "a.jpg" in res_json["deleted_files"]
    assert "b.jpg" in res_json["deleted_files"]


# =========================
# TEST: history kosong
# =========================
@patch("app.supabase")
def test_delete_profile_no_history(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_history = MagicMock(data=[])
    mock_delete_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,
        mock_history
    ]
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = mock_delete_user

    response = client.delete(f"/api/profile/petugas/{PETUGAS_UUID}")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total_history_deleted"] == 0
    assert res_json["deleted_files"] == []


# =========================
# TEST: history ada tapi gambar None
# =========================
@patch("app.supabase")
def test_delete_profile_no_image(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_history = MagicMock(data=[{"id_riwayat": "h1", "gambar": None}])
    mock_delete_history = MagicMock(data=[{"id_riwayat": "h1"}])
    mock_delete_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,
        mock_history
    ]
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.side_effect = [
        mock_delete_history,
        mock_delete_user
    ]

    response = client.delete(f"/api/profile/petugas/{PETUGAS_UUID}")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total_history_deleted"] == 1
    assert res_json["deleted_files"] == []


# =========================
# TEST: delete profile exception
# =========================
@patch("app.supabase")
def test_delete_profile_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.delete(f"/api/profile/petugas/{PETUGAS_UUID}")

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan saat menghapus profile"
