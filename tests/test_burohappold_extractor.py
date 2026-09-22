from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.burohappold import (
    BuroHappoldExtractor,
)


def test_extracts_burohappold_project_content_and_facts() -> None:
    html = """
        <html><head><title>Example Project - Buro Happold</title></head><body>
        <article class="projects sector-categories-cultural">
          <div class="wp-block-cover"><h1>Engineering a civic landmark</h1></div>
          <section><div class="bh-col-lg">
            <h2>Example Project</h2><h4>London, UK</h4>
          </div></section>
          <section><div class="bh-block-project-details__wrapper">
            <span><h5 class="label">Client</h5><p>Example Client</p></span>
            <span><h5 class="label">Duration</h5><p>Completed 2024</p></span>
            <span><h5 class="label">Services provided by Buro Happold</h5>
              <p><a>Structural engineering</a><a>Sustainability</a></p>
            </span>
          </div><div class="bh-col-lg">
            <h4>A durable and welcoming building designed for its community.</h4>
            <p>This is the complete first project paragraph with substantive
            information about the design and its context.</p>
            <p>This is the complete second project paragraph describing the
            engineering response and resulting public value.</p>
            <p>Read the full project report.</p>
          </div></section>
          <div class="kf-text">The structure reduces embodied carbon.</div>
          <div class="item award">2024 Design Award</div>
          <figcaption>View of the completed civic building.</figcaption>
        </article></body></html>
    """
    extractor = BuroHappoldExtractor(
        SiteConfig("burohappold", "https://www.burohappold.com/projects")
    )

    project = extractor.extract(
        html,
        source_url="https://www.burohappold.com/projects/example-project/",
    )

    assert project.project_name == "Example Project"
    assert project.headline == "Engineering a civic landmark"
    assert project.location_raw == "London, UK"
    assert project.client_raw == "Example Client"
    assert project.status_raw == "Completed 2024"
    assert project.services == ["Structural engineering", "Sustainability"]
    assert project.markets == ["Cultural"]
    assert "complete first project paragraph" in (project.description or "")
    assert "complete second project paragraph" in (project.description or "")
    assert "Read the full project report." in (project.description or "")
    assert project.facts["Key facts"] == "The structure reduces embodied carbon."
    assert project.facts["Awards"] == "2024 Design Award"
    assert project.facts["Image captions"] == (
        "View of the completed civic building."
    )
