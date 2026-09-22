from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.thorntontomasetti import (
    ThorntonTomasettiExtractor,
)


def test_extracts_thornton_tomasetti_project_content_and_facts() -> None:
    html = """
        <html><head><title>Example Arena | Thornton Tomasetti</title></head><body>
        <main><article class="node--type-project">
          <h1>Example Arena</h1>
          <span class="field--field_project_summary"><p>This complete summary
          describes the arena and its role in downtown redevelopment.</p></span>
          <div class="project-person"><a class="name">Alex Engineer</a></div>
          <div class="details">
            <div class="detail"><div class="field-label">Owner</div><span>Example Authority</span></div>
            <div class="detail"><div class="field-label">Location</div><span>Newark, New Jersey</span></div>
            <div class="detail"><div class="field-label">Completion Date</div><span>2025</span></div>
            <div class="detail"><div class="field-label">Area</div><span>500,000 ft²</span></div>
            <div class="awards"><p>2025 Structural Design Award</p></div>
          </div>
          <span class="field--field_body"><p>This complete overview paragraph
          explains the structural design and construction approach.</p>
          <ul><li>This complete highlight explains a major long-span roof
          engineering achievement delivered by the project team.</li></ul></span>
          <div class="field--name-field-capabilities"><div class="views-field-name">Structural Design</div></div>
          <div class="related-solutions"><span class="field--field_short_title">Sports &amp; Public Assembly</span></div>
          <figcaption><span class="field--field_photo_caption_1">Completed arena exterior.</span>
          <span class="field--field_photo_credit">Example Photographer</span></figcaption>
        </article></main></body></html>
    """
    extractor = ThorntonTomasettiExtractor(
        SiteConfig(
            "thorntontomasetti",
            "https://www.thorntontomasetti.com/work",
        )
    )

    project = extractor.extract(
        html,
        source_url="https://www.thorntontomasetti.com/project/example-arena",
    )

    assert project.project_name == "Example Arena"
    assert project.location_raw == "Newark, New Jersey"
    assert project.client_raw == "Example Authority"
    assert project.status_raw == "2025"
    assert project.size_raw == "500,000 ft²"
    assert project.services == ["Structural Design"]
    assert project.markets == ["Sports & Public Assembly"]
    assert "complete overview paragraph" in (project.description or "")
    assert "complete highlight" in (project.description or "")
    assert project.facts["Project Awards"] == "2025 Structural Design Award"
    assert project.facts["Lead contacts"] == "Alex Engineer"
    assert project.facts["Image captions"] == "Completed arena exterior."
