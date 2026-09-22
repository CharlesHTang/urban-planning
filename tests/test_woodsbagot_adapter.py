from architecture_scraper.adapters.sites.woodsbagot import WoodsBagotAdapter


def test_filters_woods_bagot_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.woodsbagot.com/projects/example/</loc></url>
      <url><loc>https://www.woodsbagot.com/news/example/</loc></url>
    </urlset>"""
    assert WoodsBagotAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.woodsbagot.com/projects/example/"
    ]
