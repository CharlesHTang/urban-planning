from architecture_scraper.adapters.sites.imeg import ImegAdapter


def test_filters_imeg_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://imegcorp.com/project/example/</loc></url>
      <url><loc>https://imegcorp.com/projects/example/</loc></url>
    </urlset>"""
    assert ImegAdapter._parse_project_sitemap(xml, 1) == [
        "https://imegcorp.com/project/example/"
    ]
