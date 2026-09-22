from architecture_scraper.adapters.sites.royalhaskoningdhv import (
    RoyalHaskoningDhvAdapter,
)


def test_filters_haskoning_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.haskoning.com/en/projects/example</loc></url>
      <url><loc>https://www.haskoning.com/en/news/example</loc></url>
    </urlset>"""
    assert RoyalHaskoningDhvAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.haskoning.com/en/projects/example"
    ]
