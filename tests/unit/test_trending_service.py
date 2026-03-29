from app.services.trending_service import TrendingService


def test_trending_service_parses_repositories() -> None:
    html = """
    <article class="Box-row">
      <h2 class="h3 lh-condensed">
        <a href="/openai/openai-python">
          <span class="text-normal">openai /</span>
          openai-python
        </a>
      </h2>
      <p class="col-9 color-fg-muted my-1 tmp-pr-4">
        Official Python library for the OpenAI API.
      </p>
      <div class="f6 color-fg-muted mt-2">
        <span itemprop="programmingLanguage">Python</span>
        <a href="/openai/openai-python/stargazers">4,321</a>
        <a href="/openai/openai-python/forks">321</a>
        <span>Built by
          <a href="/alice"><img alt="@alice" /></a>
          <a href="/bob"><img alt="@bob" /></a>
        </span>
        <span>987 stars today</span>
      </div>
    </article>
    """

    repositories = TrendingService(fetcher=lambda _: html, overviewer=lambda repos: ["OpenAI APIを扱うPythonライブラリです。"]).list_repositories()

    assert len(repositories) == 1
    assert repositories[0].owner == "openai"
    assert repositories[0].name == "openai-python"
    assert repositories[0].description == "Official Python library for the OpenAI API."
    assert repositories[0].language == "Python"
    assert repositories[0].stars == "4,321"
    assert repositories[0].forks == "321"
    assert repositories[0].stars_today == "987"
    assert repositories[0].built_by == ["alice", "bob"]
    assert repositories[0].overview_ja == "OpenAI APIを扱うPythonライブラリです。"
