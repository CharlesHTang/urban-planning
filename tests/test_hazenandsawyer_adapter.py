from architecture_scraper.adapters.sites.hazenandsawyer import (
    HazenAndSawyerAdapter,
)


def test_filters_hazen_project_urls() -> None:
    xml = """<urlset>
      <url><loc>https://www.hazenandsawyer.com/projects/example</loc></url>
      <url><loc>https://www.hazenandsawyer.com/work/example</loc></url>
    </urlset>"""
    assert HazenAndSawyerAdapter._parse_project_sitemap(xml, 1) == [
        "https://www.hazenandsawyer.com/projects/example"
    ]
