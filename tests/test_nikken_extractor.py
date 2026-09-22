from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.nikken import NikkenExtractor


def test_extracts_nikken_project_content_and_facts() -> None:
    html = """
        <html><head><title>Research Facility | PROJECTS | NIKKEN SEKKEI LTD</title>
        </head><body><main>
          <h1 class="c-project-pageHeader__hdg">Research Facility</h1>
          <div class="c-project-pageHeader__text">Tokyo, , Japan</div>
          <h2 class="p-projectsDet__detail__hdg">A flexible laboratory campus</h2>
          <div class="l-article-col__main">
            <div class="lead">This is the full first description section about
            the project brief.<br>This is the full second description section
            about the design response and its benefits.</div>
            <table><tr><th>LOCATION</th><td>Tokyo, Japan</td></tr>
              <tr><th>TOTAL FLOOR AREA</th><td>12,000 ㎡</td></tr>
              <tr><th>COMPLETION</th><td>2024</td></tr></table>
          </div>
          <div class="l-article-info"><div class="l-article-info__title">SERVICES</div>
            <div class="l-article-info__labelListItem"><a href="/en/services/architecture/">Architecture</a></div>
          </div>
          <div class="l-article-info"><div class="l-article-info__title">DOMAIN</div>
            <div class="l-article-info__labelListItem"><a href="/en/projects/?domain_id=research">Research</a></div>
          </div>
          <div class="l-article-info"><div class="l-article-info__title">AWARD</div>
            <ul><li>2024 Design Award</li></ul>
          </div>
          <ul class="c-carousel-02"><li class="c-carousel-02__item">Photo by Example Studio</li></ul>
        </main></body></html>
    """
    extractor = NikkenExtractor(
        SiteConfig("nikken", "https://www.nikken.co.jp/en/projects")
    )

    project = extractor.extract(
        html,
        source_url=(
            "https://www.nikken.jp/en/projects/research_development/"
            "research_facility.html"
        ),
    )

    assert project.project_name == "Research Facility"
    assert project.headline == "A flexible laboratory campus"
    assert project.location_raw == "Tokyo, Japan"
    assert project.status_raw == "2024"
    assert project.size_raw == "12,000 ㎡"
    assert project.services == ["Architecture"]
    assert project.markets == ["Research"]
    assert "full first description section" in (project.description or "")
    assert "full second description section" in (project.description or "")
    assert project.facts["Photo credits"] == "Photo by Example Studio"
    assert project.facts["AWARD"] == "2024 Design Award"
