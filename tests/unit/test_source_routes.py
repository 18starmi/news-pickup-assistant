from app.db.init_db import initialize_database
from app.db.session import get_connection
from app.services.source_service import SourceService
from tests.conftest import create_test_client


def test_list_sources_endpoint_returns_seeded_sources() -> None:
    initialize_database()
    with get_connection() as connection:
        SourceService(connection).sync_default_sources()

    client = create_test_client()

    response = client.get("/sources")

    assert response.status_code == 200
    assert len(response.json()) >= 5
    assert response.json()[0]["name"] == "GitHub Blog Atom"


def test_sources_view_returns_html() -> None:
    initialize_database()
    with get_connection() as connection:
        SourceService(connection).sync_default_sources()

    client = create_test_client()

    response = client.get("/sources/view")

    assert response.status_code == 200
    assert "巡回ソース" in response.text
    assert "有効ソースを一括実行" in response.text
