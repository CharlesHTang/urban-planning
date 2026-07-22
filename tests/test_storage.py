import json
from pathlib import Path

from architecture_scraper.models import RawPage
from architecture_scraper.storage import PageStore


def test_stores_raw_html_and_manifest(tmp_path: Path) -> None:
    page = RawPage(
        site="Studio One",
        kind="listing",
        requested_url="https://studio.test/work",
        url="https://studio.test/work/",
        html="<html>unparsed</html>",
    )

    with PageStore(tmp_path) as store:
        html_path = store.save(page)
        urls_path = store.save_project_urls("Studio One", ["https://studio.test/one"])

    assert html_path.read_text(encoding="utf-8") == "<html>unparsed</html>"
    assert urls_path.read_text(encoding="utf-8") == "https://studio.test/one\n"
    manifest = json.loads((tmp_path / "manifest.jsonl").read_text(encoding="utf-8"))
    assert manifest["url"] == "https://studio.test/work/"
    assert manifest["path"] == html_path.relative_to(tmp_path).as_posix()

