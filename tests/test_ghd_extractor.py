from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.ghd import GhdExtractor


def test_extracts_ghd_project_content_and_facts() -> None:
    html = """
        <html><head><title>Remote Hospital | GHD</title></head><body><main>
          <h1 class="hero-block-alternate__title">Remote Hospital</h1>
          <div class="hero-block-alternate__subtitle">Alaska, USA</div>
          <div class="hero-block-alternate__project-details">
            <p>Client: Example Health Authority</p><p>Sector: Architecture</p>
          </div>
          <ul class="tag-list"><li><a class="tag">Healthcare</a></li></ul>
          <div class="hero-block-summary">This complete overview explains the
          hospital project and the communities it serves.</div>
          <section><h2 class="content-block__title">The challenge</h2>
            <div class="content-block__description"><p>This complete challenge
            paragraph describes the severe climate and access constraints.</p></div>
          </section>
          <details class="accordion"><summary>The impact</summary>
            <div class="accordion__content"><p>This complete impact paragraph
            describes improved access to essential medical care.</p></div>
          </details>
          <figcaption class="mosaic-figcaption">Hospital entrance in winter.</figcaption>
        </main></body></html>
    """
    extractor = GhdExtractor(SiteConfig("ghd", "https://www.ghd.com/en/projects"))

    project = extractor.extract(
        html,
        source_url="https://www.ghd.com/en/projects/remote-hospital",
    )

    assert project.project_name == "Remote Hospital"
    assert project.location_raw == "Alaska, USA"
    assert project.client_raw == "Example Health Authority"
    assert project.markets == ["Architecture"]
    assert "complete overview" in (project.description or "")
    assert "complete challenge paragraph" in (project.description or "")
    assert "complete impact paragraph" in (project.description or "")
    assert project.facts["Tags"] == "Healthcare"
    assert project.facts["Image captions"] == "Hospital entrance in winter."
