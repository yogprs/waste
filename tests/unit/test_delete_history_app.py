from unittest.mock import patch, MagicMock

# =========================
# TEST: delete selected success
# =========================
@patch("app.supabase")
def test_delete_selected_success(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1", "image": "http://img.com/a.jpg"},
        {"id": "2", "image": "http://img.com/b.jpg"},
    ]

    # mock select
    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response

    # mock delete
    mock_supabase.table.return_value.delete.return_value.in_.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history/delete", json={
        "ids": ["1", "2"],
        "delete_all": False
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["mode"] == "selected"
    assert len(res_json["deleted_files"]) == 2


# =========================
# TEST: delete selected tanpa ids
# =========================
def test_delete_selected_no_ids(client):
    response = client.delete("/api/history/delete", json={
        "ids": [],
        "delete_all": False
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "No IDs provided"


# =========================
# TEST: delete all success
# =========================
@patch("app.supabase")
def test_delete_all_success(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1", "image": "http://img.com/a.jpg"}
    ]

    # select chain
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # delete chain
    mock_supabase.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history/delete", json={
        "delete_all": True,
        "id_user": "1"
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["mode"] == "all"
    assert res_json["deleted_files"] == ["a.jpg"]


# =========================
# TEST: delete all tanpa id_user
# =========================
def test_delete_all_no_user(client):
    response = client.delete("/api/history/delete", json={
        "delete_all": True
    })

    assert response.status_code == 400
    assert response.get_json()["error"] == "id_user required"


# =========================
# TEST: delete all dengan label filter
# =========================
@patch("app.supabase")
def test_delete_all_with_label(mock_supabase, client):
    mock_query = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1", "image": "http://img.com/a.jpg"}
    ]

    # select chain
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
    mock_query.eq.return_value.execute.return_value = mock_response

    # delete chain
    mock_supabase.table.return_value.delete.return_value.eq.return_value = mock_query
    mock_query.eq.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history/delete", json={
        "delete_all": True,
        "id_user": "1",
        "label": "plastic"
    })

    assert response.status_code == 200


# =========================
# TEST: tidak ada file (image kosong)
# =========================
@patch("app.supabase")
def test_delete_no_images(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1", "image": None}
    ]

    mock_supabase.table.return_value.select.return_value.in_.return_value.execute.return_value = mock_response
    mock_supabase.table.return_value.delete.return_value.in_.return_value.execute.return_value = MagicMock()

    response = client.delete("/api/history/delete", json={
        "ids": ["1"],
        "delete_all": False
    })

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["deleted_files"] == []


# =========================
# TEST: exception error
# =========================
@patch("app.supabase")
def test_delete_exception(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.delete("/api/history/delete", json={
        "ids": ["1"],
        "delete_all": False
    })

    assert response.status_code == 500
    assert "error" in response.get_json()