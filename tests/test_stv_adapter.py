from architecture_scraper.adapters.sites.stv import StvAdapter


def test_filters_stv_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://stvinc.com/project/example/</loc></url>
      <url><loc>https://stvinc.com/projects/example/</loc></url>
    </urlset>"""
    assert StvAdapter._parse_project_sitemap(xml, 1) == [
        "https://stvinc.com/project/example/"
    ]
