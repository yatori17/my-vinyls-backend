import pytest
from unittest.mock import MagicMock, patch
from flask import Flask

from external_api import init_external_routes


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def view_func():
    """Registers the route on a mocked `app` and returns the raw view function."""
    captured = {}

    def fake_get(path, **kwargs):
        def decorator(func):
            captured["func"] = func
            return func
        return decorator

    mock_app = MagicMock()
    mock_app.get.side_effect = fake_get

    init_external_routes(
        mock_app,
        vinyl_tag=None,
        ErrorSchema=None,
        ListExternalVinylSchema=None,
    )
    return captured["func"]


@pytest.fixture
def flask_app():
    """A bare Flask app, only used to open request contexts for `flask.request`."""
    return Flask(__name__)


def make_discogs_response(status_code=200, json_data=None):
    """Builds a fake `requests.Response`-like object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    return mock_resp


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_missing_query_returns_400(view_func, flask_app):
    with flask_app.test_request_context("/external-vinyl"):
        body, status = view_func()

    assert status == 400
    assert body == {"mesg": "Query parameter is required"}


@patch("external_api.requests.get")
def test_successful_search_maps_fields(mock_get, view_func, flask_app):
    mock_get.return_value = make_discogs_response(
        200,
        {
            "results": [
                {
                    "title": "Nevermind",
                    "year": "1991",
                    "genre": ["Rock"],
                    "cover_image": "http://example.com/cover.jpg",
                }
            ]
        },
    )

    with flask_app.test_request_context("/external-vinyl?query=nirvana"):
        body, status = view_func()

    assert status == 200
    assert body == {
        "results": [
            {
                "title": "Nevermind",
                "year": "1991",
                "genre": ["Rock"],
                "cover_image": "http://example.com/cover.jpg",
            }
        ]
    }


@patch("external_api.requests.get")
def test_query_and_auth_header_are_sent_correctly(mock_get, view_func, flask_app):
    mock_get.return_value = make_discogs_response(200, {"results": []})

    with flask_app.test_request_context("/external-vinyl?query=pink+floyd"):
        view_func()

    called_url = mock_get.call_args.args[0]
    called_headers = mock_get.call_args.kwargs["headers"]

    # NOTE: Flask decodes '+' in query strings back to a space, and the
    # route builds the Discogs URL with an f-string (no urlencode), so the
    # raw space ends up in the outgoing URL as-is. This is arguably a bug
    # in the route (special characters like '&' or '#' in a search term
    # would break the URL or get sent to the wrong param) - flagging it
    # here via the assertion rather than silently working around it.
    assert "q=pink floyd" in called_url
    assert called_headers["User-Agent"] == "VirtualDiggingApp/1.0"
    assert called_headers["Authorization"].startswith("Discogs token=")


@patch("external_api.requests.get")
def test_results_are_truncated_to_five(mock_get, view_func, flask_app):
    fake_results = [
        {"title": f"Album {i}", "year": "2000", "genre": [], "cover_image": None}
        for i in range(10)
    ]
    mock_get.return_value = make_discogs_response(200, {"results": fake_results})

    with flask_app.test_request_context("/external-vinyl?query=test"):
        body, status = view_func()

    assert status == 200
    assert len(body["results"]) == 5
    assert body["results"][0]["title"] == "Album 0"


@patch("external_api.requests.get")
def test_missing_optional_fields_default_gracefully(mock_get, view_func, flask_app):
    mock_get.return_value = make_discogs_response(
        200, {"results": [{"title": "No Genre Album"}]}
    )

    with flask_app.test_request_context("/external-vinyl?query=test"):
        body, status = view_func()

    assert status == 200
    result = body["results"][0]
    assert result["title"] == "No Genre Album"
    assert result["year"] is None
    assert result["genre"] == []
    assert result["cover_image"] is None


@patch("external_api.requests.get")
def test_discogs_non_200_returns_500(mock_get, view_func, flask_app):
    mock_get.return_value = make_discogs_response(404, {})

    with flask_app.test_request_context("/external-vinyl?query=test"):
        body, status = view_func()

    assert status == 500
    assert "status 404" in body["mesg"]


@patch("external_api.requests.get")
def test_requests_exception_returns_500(mock_get, view_func, flask_app):
    mock_get.side_effect = Exception("connection timed out")

    with flask_app.test_request_context("/external-vinyl?query=test"):
        body, status = view_func()

    assert status == 500
    assert "connection timed out" in body["mesg"]


@patch("external_api.requests.get")
def test_empty_results_list_returns_empty_results(mock_get, view_func, flask_app):
    mock_get.return_value = make_discogs_response(200, {"results": []})

    with flask_app.test_request_context("/external-vinyl?query=nothingfound"):
        body, status = view_func()

    assert status == 200
    assert body == {"results": []}
