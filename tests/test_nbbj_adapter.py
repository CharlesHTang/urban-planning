import json

import pytest

from architecture_scraper.adapters.sites.nbbj import NbbjAdapter


def test_parses_nbbj_embedded_project_records() -> None:
    payload = {
        "props": {
            "pageProps": {
                "finalItems": [
                    {"type": "project", "uid": "project-one"},
                    {"type": "idea", "uid": "not-a-project"},
                    {"type": "project", "uid": "project-two"},
                    {"type": "project", "uid": "project-one"},
                ]
            }
        }
    }
    html = f'<script id="__NEXT_DATA__">{json.dumps(payload)}</script>'

    assert NbbjAdapter._parse_listing(html) == [
        "https://www.nbbj.com/work/project-one",
        "https://www.nbbj.com/work/project-two",
    ]


def test_rejects_nbbj_listing_without_embedded_data() -> None:
    with pytest.raises(RuntimeError, match="__NEXT_DATA__"):
        NbbjAdapter._parse_listing("<html></html>")
