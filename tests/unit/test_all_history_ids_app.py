from unittest.mock import patch, MagicMock

# =========================
# TEST: get history success (default params)
# =========================
@patch("app.supabase")
def test_get_history_success(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1", "label": "plastic"},
        {"id": "2", "label": "glass"},
    ]
    mock_response.count = 2

    mock_supabase.table.return_value.select.return_value.eq.return_value \
        .order.return_value.range.return_value.execute.return_value = mock_response

    response = client.get("/api/history/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 1
    assert res_json["limit"] == 10
    assert res_json["total"] == 2
    assert len(res_json["data"]) == 2


# =========================
# TEST: get history dengan filter label
# =========================
@patch("app.supabase")
def test_get_history_with_label(mock_supabase, client):
    mock_query = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": "1", "label": "plastic"}]
    mock_response.count = 1

    # chaining mock
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
    mock_query.eq.return_value = mock_query  # filter label
    mock_query.order.return_value.range.return_value.execute.return_value = mock_response

    response = client.get("/api/history/1?label=plastic")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["total"] == 1
    assert res_json["data"][0]["label"] == "plastic"


# =========================
# TEST: get history pagination
# =========================
@patch("app.supabase")
def test_get_history_pagination(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "3"}]
    mock_response.count = 100

    mock_supabase.table.return_value.select.return_value.eq.return_value \
        .order.return_value.range.return_value.execute.return_value = mock_response

    response = client.get("/api/history/1?page=2&limit=1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 2
    assert res_json["limit"] == 1
    assert res_json["total"] == 100


# =========================
# TEST: get history error (exception)
# =========================
@patch("app.supabase")
def test_get_history_error(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.get("/api/history/1")

    assert response.status_code == 500
    assert "error" in response.get_json()


# =========================
# TEST: get all ids success
# =========================
@patch("app.supabase")
def test_get_all_ids_success(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [
        {"id": "1"},
        {"id": "2"},
        {"id": "3"},
    ]

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    response = client.get("/api/history/ids/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["ids"] == ["1", "2", "3"]


# =========================
# TEST: get all ids dengan filter label
# =========================
@patch("app.supabase")
def test_get_all_ids_with_label(mock_supabase, client):
    mock_query = MagicMock()
    mock_response = MagicMock()
    mock_response.data = [{"id": "10"}]

    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query
    mock_query.eq.return_value.execute.return_value = mock_response

    response = client.get("/api/history/ids/1?label=plastic")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["ids"] == ["10"]


# =========================
# TEST: get all ids kosong
# =========================
@patch("app.supabase")
def test_get_all_ids_empty(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = []

    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    response = client.get("/api/history/ids/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["ids"] == []


# =========================
# TEST: get all ids error
# =========================
@patch("app.supabase")
def test_get_all_ids_error(mock_supabase, client):
    mock_supabase.table.side_effect = Exception("DB error")

    response = client.get("/api/history/ids/1")

    assert response.status_code == 500
    assert "error" in response.get_json()