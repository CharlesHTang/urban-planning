import json

from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.dargroup import DarGroupExtractor


def test_extracts_dargroup_project_content_and_next_metadata() -> None:
    fields = {
        "brand": [{"fields": {"title": {"value": "Penspen"}}}],
        "geography": [{"fields": {"title": {"value": "Europe"}}}],
        "impact": [{"fields": {"title": {"value": "Sustainability"}}}],
        "sector": [{"fields": {"title": {"value": "Energy Transition"}}}],
        "date": {"value": "2025-05-07T21:22:00Z"},
    }
    payload = {
        "props": {
            "pageProps": {
                "layoutData": {"sitecore": {"route": {"fields": fields}}}
            }
        }
    }
    html = f"""
        <html><head><title>Hydrogen Infrastructure Analysis</title></head><body>
        <main><div id="content">
          <div class="breadcrumb-item active">Hydrogen Infrastructure Analysis</div>
          <div class="component rich-text"><div class="component-content">
            <p>This first complete paragraph explains the infrastructure project
            and why it is important to the regional energy transition.</p>
            <h2>Repurposing infrastructure</h2>
            <p>This second complete paragraph explains the engineering analysis
            and the resulting decarbonization benefits.</p>
          </div></div>
          <div class="twocolumn_content"><div class="heading">Project Details</div>
            <div class="description"><p>Location<br><strong>Berlin, Germany</strong></p></div>
          </div>
        </div></main>
        <script id="__NEXT_DATA__" type="application/json">{json.dumps(payload)}</script>
        </body></html>
    """
    extractor = DarGroupExtractor(
        SiteConfig("dargroup", "https://www.dargroup.com/work")
    )

    project = extractor.extract(
        html,
        source_url=(
            "https://sidaracollaborative.com/projects/"
            "hydrogen-infrastructure-analysis"
        ),
    )

    assert project.project_name == "Hydrogen Infrastructure Analysis"
    assert project.location_raw == "Berlin, Germany"
    assert project.markets == ["Energy Transition"]
    assert "first complete paragraph" in (project.description or "")
    assert "second complete paragraph" in (project.description or "")
    assert project.facts["Brands"] == "Penspen"
    assert project.facts["Impact"] == "Sustainability"
    assert project.facts["Published"] == "2025-05-07T21:22:00Z"
    assert project.facts["Section headings"] == [
        "Repurposing infrastructure",
        "Project Details",
    ]
