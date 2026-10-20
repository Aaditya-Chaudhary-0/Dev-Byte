from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings, _resolve_env_file
from app.main import app

client = TestClient(app)


def test_collection_routes_expose_bounded_pagination_parameters() -> None:
    schema = client.get("/openapi.json").json()
    paths = (
        "/api/students",
        "/api/mentors",
        "/api/skills",
        "/api/students/me/skills",
        "/api/students/me/learning-goals",
        "/api/projects/me",
        "/api/teams",
        "/api/hackathons/me/bookmarks",
    )

    for path in paths:
        parameters = {
            parameter["name"]: parameter
            for parameter in schema["paths"][path]["get"]["parameters"]
        }
        assert parameters["page"]["schema"]["minimum"] == 1
        assert parameters["page_size"]["schema"]["maximum"] == 100


def test_pagination_rejects_invalid_bounds_without_changing_list_shape() -> None:
    assert client.get("/api/students?page=0").status_code == 422
    assert client.get("/api/students?page_size=101").status_code == 422

    response = client.get("/api/students?page=1&page_size=1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) <= 1


def test_cors_allows_vite_origin_and_only_supported_methods() -> None:
    response = client.options(
        "/api/auth/me",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "PATCH" in response.headers["access-control-allow-methods"]
    assert "PUT" not in response.headers["access-control-allow-methods"]


def test_openapi_uses_unversioned_api_paths() -> None:
    schema = client.get("/openapi.json").json()

    assert schema["openapi"].startswith("3.")
    assert any(path.startswith("/api/") for path in schema["paths"])
    assert not any(path.startswith("/api/v1/") for path in schema["paths"])
    assert client.get("/docs").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_runtime_secrets_are_required_and_example_files_are_not_loaded() -> None:
    env_file = _resolve_env_file()

    assert Settings.model_fields["database_url"].is_required()
    assert Settings.model_fields["jwt_secret"].is_required()
    assert env_file is None or Path(env_file).name == ".env"
