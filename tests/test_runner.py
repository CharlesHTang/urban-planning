from pathlib import Path

from architecture_scraper.config import SiteConfig
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
