from unittest.mock import patch, MagicMock

ADMIN_UUID = "93fdf758-38da-401c-8440-a8b8af2431c3"
PETUGAS_UUID = "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d"
NASABAH_UUID = "f1e2d3c4-b5a6-4987-9876-543210fedcba"

# =========================
# TEST: jenis user tidak valid
# =========================
def test_get_history_invalid_user_type(client):
    response = client.get(f"/api/history/guest/{PETUGAS_UUID}")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Jenis akun tidak valid"


# =========================
# TEST: UUID tidak valid
# =========================
def test_get_history_invalid_uuid(client):
    response = client.get("/api/history/petugas/invalid-uuid")

    assert response.status_code == 400
    assert response.get_json()["error"] == "Format ID User tidak valid"


# =========================
# TEST: user tidak ditemukan di database
# =========================
@patch("app.supabase")
def test_get_history_user_not_found(mock_supabase, client):
    mock_empty = MagicMock(data=[])
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_empty

    response = client.get(f"/api/history/petugas/{PETUGAS_UUID}")

    assert response.status_code == 403
    assert response.get_json()["error"] == "Akun tidak ditemukan atau tidak memiliki akses"


# =========================
# TEST: success default (tanpa query param)
# =========================
@patch("app.supabase")
def test_get_history_default(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_petugas": PETUGAS_UUID}])
    mock_history_res = MagicMock()
    mock_history_res.data = [{
        "id_riwayat": "h1",
        "label": "Organik",
        "akurasi": 95.5,
        "gambar": "http://img.com/a.jpg",
        "id_petugas": PETUGAS_UUID,
        "id_admin": None,
        "id_nasabah": None,
        "dibuat_pada": "2026-11-01T10:00:00Z"
    }]
    mock_history_res.count = 1

    mock_names_res = MagicMock(data=[{"id_petugas": PETUGAS_UUID, "nama": "Budi Petugas"}])

    # 1st call: check user, 2nd call: riwayat query, 3rd call: batch user names
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.in_.return_value = mock_query

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "petugas":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
            mock_t.select.return_value.in_.return_value.execute.return_value = mock_names_res
        elif table_name == "riwayat":
            mock_t.select.return_value = mock_query
            mock_query.execute.return_value = mock_history_res
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.get(f"/api/history/petugas/{PETUGAS_UUID}")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 1
    assert res_json["limit"] == 10
    assert res_json["total"] == 1
    assert len(res_json["data"]) == 1
    assert res_json["data"][0]["user_name"] == "Budi Petugas"
    assert res_json["data"][0]["user_type"] == "petugas"


# =========================
# TEST: dengan pagination & limit
# =========================
@patch("app.supabase")
def test_get_history_with_pagination(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_history_res = MagicMock()
    mock_history_res.data = [{
        "id_riwayat": "h2",
        "label": "Non-Organik",
        "akurasi": 88.0,
        "gambar": "http://img.com/b.jpg",
        "id_admin": ADMIN_UUID,
        "id_petugas": None,
        "id_nasabah": None,
        "dibuat_pada": "2026-11-01T10:00:00Z"
    }]
    mock_history_res.count = 25

    mock_names_res = MagicMock(data=[{"id_admin": ADMIN_UUID, "nama": "Admin Sistem"}])

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
            mock_t.select.return_value.in_.return_value.execute.return_value = mock_names_res
        elif table_name == "riwayat":
            mock_t.select.return_value = mock_query
            mock_query.execute.return_value = mock_history_res
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.get(f"/api/history/admin/{ADMIN_UUID}?page=2&limit=5")
    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 2
    assert res_json["limit"] == 5
    assert res_json["total"] == 25
    assert res_json["total_page"] == 5


# =========================
# TEST: filter label
# =========================
@patch("app.supabase")
def test_get_history_filter_label(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_nasabah": NASABAH_UUID}])
    mock_history_res = MagicMock()
    mock_history_res.data = []
    mock_history_res.count = 0

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_history_res

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "nasabah":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
        elif table_name == "riwayat":
            mock_t.select.return_value = mock_query
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.get(f"/api/history/nasabah/{NASABAH_UUID}?label=Organik")
    assert response.status_code == 200
    # verify eq("label", "Organik") called
    mock_query.eq.assert_any_call("label", "Organik")


# =========================
# TEST: sorting asc
# =========================
@patch("app.supabase")
def test_get_history_sort_asc(mock_supabase, client):
    mock_user = MagicMock(data=[{"id_admin": ADMIN_UUID}])
    mock_history_res = MagicMock(data=[], count=0)

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_history_res

    def table_router(table_name):
        mock_t = MagicMock()
        if table_name == "admin":
            mock_t.select.return_value.eq.return_value.execute.return_value = mock_user
        elif table_name == "riwayat":
            mock_t.select.return_value = mock_query
        return mock_t

    mock_supabase.table.side_effect = table_router

    response = client.get(f"/api/history/admin/{ADMIN_UUID}?order=asc")
    assert response.status_code == 200
    mock_query.order.assert_called_with("dibuat_pada", desc=False)


# =========================
# TEST: history exception
# =========================
@patch("app.supabase")
def test_get_history_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.get(f"/api/history/admin/{ADMIN_UUID}")

    assert response.status_code == 500
    assert response.get_json()["error"] == "Terjadi kesalahan saat mengambil riwayat"
