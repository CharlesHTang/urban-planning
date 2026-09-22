from architecture_scraper.adapters.sites.bharchitects import BhArchitectsAdapter


def test_filters_bh_project_urls_and_accepts_leading_whitespace() -> None:
    xml = """
      <?xml version="1.0"?>
      <urlset>
        <url><loc>https://bharchitects.com/en/project/example/</loc></url>
        <url><loc>https://bharchitects.com/en/projects/</loc></url>
      </urlset>"""
    assert BhArchitectsAdapter._parse_project_sitemap(xml, 1) == [
        "https://bharchitects.com/en/project/example/"
    ]
