from architecture_scraper.adapters.sites.aedas import AedasAdapter


def test_filters_aedas_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.aedas.com/en/project/example/</loc></url>
      <url><loc>https://www.aedas.com/en/architecture/</loc></url>
    </urlset>"""
    assert AedasAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.aedas.com/en/project/example/"
    ]
