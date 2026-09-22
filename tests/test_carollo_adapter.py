from architecture_scraper.adapters.sites.carollo import CarolloAdapter


def test_filters_carollo_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://carollo.com/solutions/example/</loc></url>
      <url><loc>https://carollo.com/expertise/example/</loc></url>
    </urlset>"""
    assert CarolloAdapter._parse_project_sitemap(xml, 1) == [
        "https://carollo.com/solutions/example/"
    ]
