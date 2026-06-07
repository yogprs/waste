from unittest.mock import patch, MagicMock

# =========================
# TEST: user tidak ditemukan
# =========================
@patch("app.supabase")
def test_delete_profile_user_not_found(mock_supabase, client):
    mock_user = MagicMock()
    mock_user.data = []

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_user

    response = client.delete("/api/profile/1")

    assert response.status_code == 404
    assert response.get_json()["error"] == "User tidak ditemukan"


# =========================
# TEST: delete profile success
# =========================
@patch("app.supabase")
def test_delete_profile_success(mock_supabase, client):
    # STEP 1: user ditemukan
    mock_user = MagicMock()
    mock_user.data = [{"id": "1"}]

    # STEP 2: history user
    mock_history = MagicMock()
    mock_history.data = [
        {"id": "h1", "image": "http://img.com/a.jpg"},
        {"id": "h2", "image": "http://img.com/b.jpg"},
    ]

    # mock chain users select
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,    # first call (users)
        mock_history  # second call (history)
    ]

    # mock delete history
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    # mock storage remove
    mock_supabase.storage.from_.return_value.remove.return_value = None

    response = client.delete("/api/profile/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total_history_deleted"] == 2
    assert res_json["deleted_files"] == ["a.jpg", "b.jpg"]


# =========================
# TEST: history kosong (tidak ada file)
# =========================
@patch("app.supabase")
def test_delete_profile_no_history(mock_supabase, client):
    mock_user = MagicMock()
    mock_user.data = [{"id": "1"}]

    mock_history = MagicMock()
    mock_history.data = []

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,
        mock_history
    ]

    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/profile/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total_history_deleted"] == 0
    assert res_json["deleted_files"] == []


# =========================
# TEST: history ada tapi image None
# =========================
@patch("app.supabase")
def test_delete_profile_no_image(mock_supabase, client):
    mock_user = MagicMock()
    mock_user.data = [{"id": "1"}]

    mock_history = MagicMock()
    mock_history.data = [
        {"id": "h1", "image": None}
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
        mock_user,
        mock_history
    ]

    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/profile/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["deleted_files"] == []


# =========================
# TEST: exception error
# =========================
@patch("app.supabase")
def test_delete_profile_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.delete("/api/profile/1")

    assert response.status_code == 500
    assert "error" in response.get_json()