import asyncio
from pathlib import Path

import pytest

from architecture_scraper.config import SiteConfig
from architecture_scraper.fetcher import FetchResult
from architecture_scraper.models import DiscoveryResult, RawPage, RunSummary
from architecture_scraper.runner import CollectionRunner
from architecture_scraper.storage import PageStore


def test_normalizes_relative_urls_and_removes_duplicates(tmp_path: Path) -> None:
    config = SiteConfig("studio", "https://studio.test/work/")

    with PageStore(tmp_path) as store:
        runner = CollectionRunner(config, store)
        urls, errors = runner._normalize_urls(
            [
                "one#top",
                "https://studio.test/work/two",
                "one",
                "mailto:test@test.test",
                "",
            ]
        )

    assert urls == [
        "https://studio.test/work/one",
        "https://studio.test/work/two",
    ]
    assert len(errors) == 2


def test_resume_fetches_only_missing_and_empty_detail_pages(tmp_path: Path) -> None:
    config = SiteConfig("studio", "https://studio.test/work/")
    completed_url = "https://studio.test/work/completed"
    empty_url = "https://studio.test/work/empty"
    missing_url = "https://studio.test/work/missing"
    fetched_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, url: str, *, render: str) -> FetchResult:
            fetched_urls.append(url)
            assert render == "never"
            return FetchResult(url, url, f"<html>{url}</html>")

    async def exercise() -> tuple[int, int]:
        with PageStore(tmp_path) as store:
            store.save(
                RawPage(
                    "studio",
                    "detail",
                    completed_url,
                    completed_url,
                    "<html>complete</html>",
                )
            )
            store.save(
                RawPage("studio", "detail", empty_url, empty_url, "")
            )
            runner = CollectionRunner(config, store)
            saved, skipped, errors = await runner._fetch_details(
                [completed_url, empty_url, missing_url],
                FakeFetcher(),  # type: ignore[arg-type]
                resume=True,
            )
            assert errors == []
            return saved, skipped

    saved, skipped = asyncio.run(exercise())

    assert saved == 2
    assert skipped == 1
    assert fetched_urls == [empty_url, missing_url]


def test_normal_mode_refetches_existing_detail_page(tmp_path: Path) -> None:
    config = SiteConfig("studio", "https://studio.test/work/")
    url = "https://studio.test/work/project-one"
    fetched_urls: list[str] = []

    class FakeFetcher:
        async def fetch(self, requested_url: str, *, render: str) -> FetchResult:
            fetched_urls.append(requested_url)
            return FetchResult(requested_url, requested_url, "<html>fresh</html>")

    async def exercise() -> tuple[int, int]:
        with PageStore(tmp_path) as store:
            store.save(RawPage("studio", "detail", url, url, "<html>old</html>"))
            runner = CollectionRunner(config, store)
            saved, skipped, errors = await runner._fetch_details(
                [url],
                FakeFetcher(),  # type: ignore[arg-type]
            )
            assert errors == []
            return saved, skipped

    saved, skipped = asyncio.run(exercise())

    assert saved == 1
    assert skipped == 0
    assert fetched_urls == [url]


def test_collect_resume_still_rediscovers_and_saves_all_project_urls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = SiteConfig("studio", "https://studio.test/work/")
    completed_url = "https://studio.test/work/completed"
    new_url = "https://studio.test/work/new"
    discovery_calls = 0
    fetched_urls: list[str] = []

    class FakeAdapter:
        async def discover(self, fetcher: object) -> DiscoveryResult:
            nonlocal discovery_calls
            discovery_calls += 1
            return DiscoveryResult(
                [
                    RawPage(
                        "studio",
                        "listing",
                        config.projects_url,
                        config.projects_url,
                        "<html>listing</html>",
                    )
                ],
                [completed_url, new_url],
            )

    class FakeFetcher:
        async def __aenter__(self) -> "FakeFetcher":
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def fetch(self, url: str, *, render: str) -> FetchResult:
            fetched_urls.append(url)
            return FetchResult(url, url, "<html>new</html>")

    fake_fetcher = FakeFetcher()
    monkeypatch.setattr(
        "architecture_scraper.runner.load_adapter",
        lambda _: FakeAdapter(),
    )
    monkeypatch.setattr(CollectionRunner, "_new_fetcher", lambda _: fake_fetcher)

    async def exercise() -> RunSummary:
        with PageStore(tmp_path) as store:
            store.save(
                RawPage(
                    "studio",
                    "detail",
                    completed_url,
                    completed_url,
                    "<html>complete</html>",
                )
            )
            return await CollectionRunner(config, store).collect(resume=True)

    summary = asyncio.run(exercise())

    assert discovery_calls == 1
    assert fetched_urls == [new_url]
    assert summary.saved_pages == 2  # One listing and one new detail page.
    assert summary.skipped_pages == 1
    assert summary.discovered_urls == 2
    assert (tmp_path / "studio" / "project_urls.txt").read_text() == (
        f"{completed_url}\n{new_url}\n"
    )
