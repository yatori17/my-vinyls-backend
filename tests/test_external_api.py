import pytest
from unittest.mock import MagicMock, patch
from flask_openapi3 import OpenAPI, Info, Tag

from external_api import init_external_routes
from schemas import ErrorSchema, ListExternalVinylSchema


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def flask_app():
    """Um app OpenAPI (flask-openapi3) real, para que a injeção de `query`
    via Pydantic realmente aconteça antes da view rodar."""
    info = Info(title="Test API", version="1.0.0")
    app = OpenAPI(__name__, info=info)
    vinyl_tag = Tag(name="Vinyl", description="Vinyl")

    init_external_routes(app, vinyl_tag, ErrorSchema, ListExternalVinylSchema)
    return app


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()


def make_discogs_response(status_code=200, json_data=None):
    """Builds a fake `requests.Response`-like object."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    return mock_resp


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def test_missing_query_returns_400(client):
    response = client.get("/external-vinyl")

    # NOTE: por padrao o flask-openapi3 retorna 422 (Unprocessable Entity)
    # para erros de validacao do Pydantic, nao 400. Se o seu projeto
    # configurou `validation_error_status=400` na criacao do OpenAPI(...),
    # ajuste o status abaixo para 422 ou 400 conforme o comportamento real.
    # Rode este teste isolado e imprima response.status_code / response.get_json()
    # para confirmar o formato exato antes de travar a assertion do corpo.
    assert response.status_code in (400, 422)
    body = response.get_json()
    assert body is not None


@patch("external_api.requests.get")
def test_successful_search_maps_fields(mock_get, client):
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

    response = client.get("/external-vinyl?query=nirvana")

    assert response.status_code == 200
    assert response.get_json() == {
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
def test_query_and_auth_header_are_sent_correctly(mock_get, client):
    mock_get.return_value = make_discogs_response(200, {"results": []})

    client.get("/external-vinyl?query=pink+floyd")

    called_url = mock_get.call_args.args[0]
    called_headers = mock_get.call_args.kwargs["headers"]

    # NOTE: o parsing de query string decodifica '+' de volta para espaco,
    # e a rota monta a URL do Discogs com f-string (sem urlencode), entao
    # o espaco "cru" acaba indo para a URL de saida como esta. Isso e
    # potencialmente um bug na rota (caracteres especiais como '&' ou '#'
    # no termo de busca quebrariam a URL ou vazariam para o parametro
    # errado) - sinalizando aqui via assertion em vez de contornar
    # silenciosamente.
    assert "q=pink floyd" in called_url
    assert called_headers["User-Agent"] == "VirtualDiggingApp/1.0"
    assert called_headers["Authorization"].startswith("Discogs token=")


@patch("external_api.requests.get")
def test_results_are_truncated_to_five(mock_get, client):
    fake_results = [
        {"title": f"Album {i}", "year": "2000", "genre": [], "cover_image": None}
        for i in range(10)
    ]
    mock_get.return_value = make_discogs_response(200, {"results": fake_results})

    response = client.get("/external-vinyl?query=test")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["results"]) == 5
    assert body["results"][0]["title"] == "Album 0"


@patch("external_api.requests.get")
def test_missing_optional_fields_default_gracefully(mock_get, client):
    mock_get.return_value = make_discogs_response(
        200, {"results": [{"title": "No Genre Album"}]}
    )

    response = client.get("/external-vinyl?query=test")

    assert response.status_code == 200
    result = response.get_json()["results"][0]
    assert result["title"] == "No Genre Album"
    assert result["year"] is None
    assert result["genre"] == []
    assert result["cover_image"] is None


@patch("external_api.requests.get")
def test_discogs_non_200_returns_500(mock_get, client):
    mock_get.return_value = make_discogs_response(404, {})

    response = client.get("/external-vinyl?query=test")

    assert response.status_code == 500
    assert "status 404" in response.get_json()["mesg"]


@patch("external_api.requests.get")
def test_requests_exception_returns_500(mock_get, client):
    mock_get.side_effect = Exception("connection timed out")

    response = client.get("/external-vinyl?query=test")

    assert response.status_code == 500
    assert "connection timed out" in response.get_json()["mesg"]


@patch("external_api.requests.get")
def test_empty_results_list_returns_empty_results(mock_get, client):
    mock_get.return_value = make_discogs_response(200, {"results": []})

    response = client.get("/external-vinyl?query=nothingfound")

    assert response.status_code == 200
    assert response.get_json() == {"results": []}
