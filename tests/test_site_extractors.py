import json
from pathlib import Path

from architecture_scraper.config import SiteConfig, load_sites
from architecture_scraper.extractors.loader import load_extractor
from architecture_scraper.extractors.sites.arcadis import ArcadisExtractor
from architecture_scraper.extractors.sites.stantec import StantecExtractor


DOWNLOADED_SITES = {
    "aecom",
    "arcadis",
    "arup",
    "atkinsrealis",
    "dlrgroup",
    "gensler",
    "hdr",
    "hok",
    "jacobs",
    "mottmac",
    "perkinseastman",
    "perkinswill",
    "populous",
    "ramboll",
    "smithgroup",
    "som",
    "stantec",
    "sweco",
    "wsp",
}


def test_every_downloaded_site_has_an_importable_extractor() -> None:
    sites = {site.name: site for site in load_sites(Path("sites.yml"))}

    assert all(sites[name].extractor for name in DOWNLOADED_SITES)
    assert all(load_extractor(sites[name]) for name in DOWNLOADED_SITES)


def test_arcadis_extracts_embedded_project_data() -> None:
    data = {
        "heading": "<p>Designing a resilient waterfront</p>",
        "clientName": "Example Client",
        "location": {"address": {"country": "Example Country"}},
        "industrySector": [{"title": "Water"}],
        "challengeSummary": "<p>A sufficiently complete challenge summary.</p>",
        "challengeDetail": [],
        "solutionSummary": "<p>A sufficiently complete project solution.</p>",
        "solutionDetail": [],
        "impactSummary": "",
        "impactDetail": [],
        "impactAdditional": [],
    }
    html = (
        "<html><head><title>Waterfront project | Project | Arcadis</title></head>"
        "<body><script>React.createElement(Components.ProjectPage,"
        f"{json.dumps(data)}));</script></body></html>"
    )
    config = SiteConfig("arcadis", "https://www.arcadis.com/en/projects")

    project = ArcadisExtractor(config).extract(
        html,
        source_url="https://www.arcadis.com/en-us/projects/example/waterfront",
    )

    assert project.project_name == "Waterfront project"
    assert project.headline == "Designing a resilient waterfront"
    assert project.location_raw == "Example Country"
    assert project.client_raw == "Example Client"
    assert project.markets == ["Water"]
    assert "project solution" in (project.description or "")


def test_stantec_extracts_json_templates_and_body_html() -> None:
    project_info = {
        "location": "Example City",
        "status": "Complete",
        "listClients": [{"clientName": "Example Client"}],
        "detailItems": [],
    }
    project_tags = {
        "tagFilter": "service,discipline",
        "dataTags": [{"title": "Architecture"}],
    }
    html = f"""
        <html><head><title>Example Project | Stantec</title></head><body>
        <div class="react-mount" data-react-component="ProjectInfo">
          <template type="application/json">{json.dumps(project_info)}</template>
        </div>
        <div class="react-mount" data-react-component="ProjectTags">
          <template type="application/json">{json.dumps(project_tags)}</template>
        </div>
        <template type="application/json">{{"text": "<p>This is a complete
        project description with enough substantive detail.</p>"}}</template>
        </body></html>
    """
    config = SiteConfig("stantec", "https://www.stantec.com/en/projects")

    project = StantecExtractor(config).extract(
        html,
        source_url=(
            "https://www.stantec.com/en/projects/"
            "united-states-projects/e/example-project"
        ),
    )

    assert project.project_name == "Example Project"
    assert project.description == (
        "This is a complete project description with enough substantive detail."
    )
    assert project.location_raw == "Example City"
    assert project.client_raw == "Example Client"
    assert project.status_raw == "Complete"
    assert project.services == ["Architecture"]
