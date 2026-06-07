from unittest.mock import patch, MagicMock

# =========================
# TEST: success default (tanpa query param)
# =========================
@patch("app.supabase")
def test_get_history_default(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "1", "label": "plastic"}]
    mock_response.count = 1

    # chain mock
    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_response

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 1
    assert res_json["limit"] == 10
    assert res_json["total"] == 1
    assert len(res_json["data"]) == 1


# =========================
# TEST: dengan pagination
# =========================
@patch("app.supabase")
def test_get_history_with_pagination(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{"id": "2"}]
    mock_response.count = 20

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_response

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1?page=2&limit=5")

    res_json = response.get_json()

    assert response.status_code == 200
    assert res_json["page"] == 2
    assert res_json["limit"] == 5
    assert res_json["total"] == 20


# =========================
# TEST: filter label
# =========================
@patch("app.supabase")
def test_get_history_filter_label(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = [{"label": "plastic"}]
    mock_response.count = 1

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_response

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1?label=plastic")

    assert response.status_code == 200

    # pastikan filter label dipanggil
    mock_query.eq.assert_any_call("label", "plastic")


# =========================
# TEST: sorting asc
# =========================
@patch("app.supabase")
def test_get_history_sort_asc(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_response

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1?sort_by=label&order=asc")

    assert response.status_code == 200

    # pastikan order dipanggil dengan desc=False
    mock_query.order.assert_called_with("label", desc=False)


# =========================
# TEST: sorting desc (default)
# =========================
@patch("app.supabase")
def test_get_history_sort_desc(mock_supabase, client):
    mock_response = MagicMock()
    mock_response.data = []
    mock_response.count = 0

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.range.return_value = mock_query
    mock_query.execute.return_value = mock_response

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1")

    assert response.status_code == 200

    mock_query.order.assert_called_with("created_at", desc=True)


# =========================
# TEST: error handling (exception)
# =========================
@patch("app.supabase")
def test_get_history_exception(mock_supabase, client):
    mock_query = MagicMock()
    mock_query.select.side_effect = Exception("DB Error")

    mock_supabase.table.return_value = mock_query

    response = client.get("/api/history/1")

    res_json = response.get_json()

    assert response.status_code == 500
    assert "error" in res_json