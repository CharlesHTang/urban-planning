from architecture_scraper.adapters.sites.mbakerintl import MBakerIntlAdapter


def test_filters_michael_baker_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://mbakerintl.com/projects/example/</loc></url>
      <url><loc>https://mbakerintl.com/news/example/</loc></url>
    </urlset>"""
    assert MBakerIntlAdapter._parse_project_sitemap(xml, 1) == [
        "https://mbakerintl.com/projects/example/"
    ]
