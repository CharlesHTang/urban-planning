from architecture_scraper.adapters.sites.systra import SystraAdapter


def test_filters_systra_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.systra.com/en/projects/example/</loc></url>
      <url><loc>https://www.systra.com/en/news/example/</loc></url>
    </urlset>"""
    assert SystraAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.systra.com/en/projects/example/"
    ]
