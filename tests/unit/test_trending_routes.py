from app.api.routes import trending as trending_routes
from app.services.trending_service import TrendingRepository
from tests.conftest import create_test_client


def test_trending_view_returns_html(monkeypatch) -> None:
    def fake_list_repositories(self, limit: int = 12):  # noqa: ARG001
        return [
            TrendingRepository(
                owner="openai",
                name="openai-python",
                url="https://github.com/openai/openai-python",
                description="Official Python library for the OpenAI API.",
                language="Python",
                stars="4,321",
                forks="321",
                stars_today="987",
                built_by=["alice", "bob"],
                overview_ja="OpenAI APIを扱うPythonライブラリです。",
            )
        ]

    monkeypatch.setattr(trending_routes.TrendingService, "list_repositories", fake_list_repositories)
    client = create_test_client()

    response = client.get("/trending/view")

    assert response.status_code == 200
    assert "GitHub 技術トレンド" in response.text
    assert "openai/openai-python" in response.text
    assert "OpenAI APIを扱うPythonライブラリです。" in response.text
    assert "987 stars today" in response.text
