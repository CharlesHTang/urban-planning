from architecture_scraper.adapters.sites.bv import BvAdapter


def test_filters_black_and_veatch_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.bv.com/projects/example</loc></url>
      <url><loc>https://www.bv.com/en-US/projects/example</loc></url>
    </urlset>"""
    assert BvAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.bv.com/projects/example"
    ]
