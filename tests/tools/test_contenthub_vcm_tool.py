import json

from unittest.mock import MagicMock


def _response(data):
    response = MagicMock()
    response.json.return_value = data
    response.raise_for_status.return_value = None
    return response


def test_list_active_agreements_uses_status_filter(monkeypatch):
    import tools.contenthub_vcm_tool as tool

    calls = []

    def fake_post_json(_client, _base_url, _headers, path, payload):
        calls.append((path, payload))
        return _response([{"_id": "a1", "name": "Convenio A", "status": "activo"}])

    monkeypatch.setenv("CONTENTHUB_CONVEX_SITE_URL", "https://contenthub.test")
    monkeypatch.setenv("CONTENTHUB_CONVEX_API_KEY", "secret")
    monkeypatch.setattr(tool, "_post_json", fake_post_json)

    result = json.loads(tool.contenthub_vcm_query(operation="list", entity="agreements", query="active"))

    assert calls == [
        (
            "/hermes/crud/list",
            {"table": "agreements", "filters": {"status": "activo"}, "limit": 200},
        )
    ]
    assert result["data"] == [{"_id": "a1", "name": "Convenio A", "status": "activo"}]


def test_list_pending_content_proposals_maps_status_alias_for_any_status_entity(monkeypatch):
    import tools.contenthub_vcm_tool as tool

    calls = []

    def fake_post_json(_client, _base_url, _headers, path, payload):
        calls.append((path, payload))
        return _response([{"_id": "p1", "channel": "linkedin", "status": "pendiente"}])

    monkeypatch.setenv("CONTENTHUB_CONVEX_SITE_URL", "https://contenthub.test")
    monkeypatch.setenv("CONTENTHUB_CONVEX_API_KEY", "secret")
    monkeypatch.setattr(tool, "_post_json", fake_post_json)

    result = json.loads(tool.contenthub_vcm_query(operation="list", entity="contentProposals", query="pendientes"))

    assert calls[0][1]["filters"] == {"status": "pendiente"}
    assert result["data"][0]["status"] == "pendiente"


def test_search_with_status_alias_uses_crud_list_instead_of_text_search(monkeypatch):
    import tools.contenthub_vcm_tool as tool

    calls = []

    def fake_post_json(_client, _base_url, _headers, path, payload):
        calls.append((path, payload))
        return _response([])

    monkeypatch.setenv("CONTENTHUB_CONVEX_SITE_URL", "https://contenthub.test")
    monkeypatch.setenv("CONTENTHUB_CONVEX_API_KEY", "secret")
    monkeypatch.setattr(tool, "_post_json", fake_post_json)

    tool.contenthub_vcm_query(operation="search", entity="agreements", query="vigente")

    assert calls == [
        (
            "/hermes/crud/list",
            {"table": "agreements", "filters": {"status": "activo"}, "limit": 200},
        )
    ]


def test_list_all_query_does_not_require_search_text(monkeypatch):
    import tools.contenthub_vcm_tool as tool

    calls = []

    def fake_post_json(_client, _base_url, _headers, path, payload):
        calls.append((path, payload))
        return _response([{"_id": "a1", "name": "Convenio A"}])

    monkeypatch.setenv("CONTENTHUB_CONVEX_SITE_URL", "https://contenthub.test")
    monkeypatch.setenv("CONTENTHUB_CONVEX_API_KEY", "secret")
    monkeypatch.setattr(tool, "_post_json", fake_post_json)

    result = json.loads(tool.contenthub_vcm_query(operation="list", entity="agreements", query="listar todos"))

    assert calls[0][1] == {"table": "agreements", "filters": {}, "limit": 200}
    assert result["data"] == [{"_id": "a1", "name": "Convenio A"}]


def test_rich_operator_filters_are_applied_after_broad_server_read(monkeypatch):
    import tools.contenthub_vcm_tool as tool

    calls = []

    def fake_post_json(_client, _base_url, _headers, path, payload):
        calls.append((path, payload))
        return _response(
            [
                {"_id": "a1", "name": "Convenio A", "region": "Valparaiso", "status": "activo"},
                {"_id": "a2", "name": "Convenio B", "region": "Santiago", "status": "activo"},
                {"_id": "a3", "name": "Convenio C", "region": "Valparaiso", "status": "cerrado"},
            ]
        )

    monkeypatch.setenv("CONTENTHUB_CONVEX_SITE_URL", "https://contenthub.test")
    monkeypatch.setenv("CONTENTHUB_CONVEX_API_KEY", "secret")
    monkeypatch.setattr(tool, "_post_json", fake_post_json)

    result = json.loads(
        tool.contenthub_vcm_query(
            operation="list",
            entity="agreements",
            filters={"region": {"$contains": "valparaiso"}, "status": {"$ne": "cerrado"}},
            fields=["name", "status"],
        )
    )

    assert calls[0][1]["filters"] == {}
    assert result["data"] == [{"_id": "a1", "name": "Convenio A", "status": "activo"}]
