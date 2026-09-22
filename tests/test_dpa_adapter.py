from architecture_scraper.adapters.sites.dpa import DpaAdapter


def test_filters_dpa_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.dpa.com.sg/projects/example/</loc></url>
      <url><loc>https://www.dpa.com.sg/news/example/</loc></url>
    </urlset>"""
    assert DpaAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.dpa.com.sg/projects/example/"
    ]
