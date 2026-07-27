import asyncio

import pytest

from architecture_scraper.adapters.sites.jacobs import JacobsAdapter
from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult


def make_config() -> SiteConfig:
    return SiteConfig(
        "jacobs",
        "https://www.jacobs.com/projects",
        adapter="architecture_scraper.adapters.sites.jacobs:JacobsAdapter",
    )


def test_discovers_unique_projects_from_all_listing_pages() -> None:
    pages = {
        "https://www.jacobs.com/projects": """
            <a href="/projects/featured-project">Featured</a>
            <a href="/projects/project-one">Project one</a>
            <a href="/projects/project-one#details">Duplicate</a>
            <a href="/projects">Project root</a>
            <a href="/projects/not-a-detail/child">Nested page</a>
            <a href="https://example.com/projects/wrong-host">Wrong host</a>
            <a href="?page=1">Next</a>
            <a href="?page=2">Last</a>
        """,
        "https://www.jacobs.com/projects?page=1": """
            <a href="/projects/featured-project">Repeated featured</a>
            <a href="/projects/project-two?source=listing">Project two</a>
        """,
        "https://www.jacobs.com/projects?page=2": """
            <a href="https://www.jacobs.com/projects/project-three/">
                Project three
            </a>
        """,
    }
    requested_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            requested_urls.append(url)
            assert render == "never"
            return FetchResult(url, url, pages[url])

    async def exercise() -> None:
        result = await JacobsAdapter(make_config()).discover(
            FakeFetcher()  # type: ignore[arg-type]
        )

        assert result.project_urls == [
            "https://www.jacobs.com/projects/featured-project",
            "https://www.jacobs.com/projects/project-one",
            "https://www.jacobs.com/projects/project-two",
            "https://www.jacobs.com/projects/project-three",
        ]
        assert len(result.listing_pages) == 3
        assert [
            page.requested_url for page in result.listing_pages
        ] == requested_urls

    asyncio.run(exercise())

    assert requested_urls == [
        "https://www.jacobs.com/projects",
        "https://www.jacobs.com/projects?page=1",
        "https://www.jacobs.com/projects?page=2",
    ]


def test_rejects_listing_without_project_urls() -> None:
    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            return FetchResult(url, url, '<a href="/projects">Projects</a>')

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="no project detail URLs"):
            await JacobsAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())


def test_rejects_unreasonable_page_count() -> None:
    html = """
        <a href="/projects/project-one">Project one</a>
        <a href="/projects?page=100">Last</a>
    """

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            return FetchResult(url, url, html)

    async def exercise() -> None:
        with pytest.raises(RuntimeError, match="exceeded 100 pages"):
            await JacobsAdapter(make_config()).discover(
                FakeFetcher()  # type: ignore[arg-type]
            )

    asyncio.run(exercise())
