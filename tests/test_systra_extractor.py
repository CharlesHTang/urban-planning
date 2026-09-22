from architecture_scraper.config import SiteConfig
from architecture_scraper.extractors.sites.systra import SystraExtractor


def test_extracts_systra_markdown_response() -> None:
    markdown = """---
title: Example Project
project-market:
  - Buildings
project-service:
  - Design
project-location:
  - France
---

# Example Project

![Example](https://example.com/image.jpg)

**A substantive introductory description for the example project.**

The remaining project narrative is retained as a second paragraph.
"""

    project = SystraExtractor(
        SiteConfig("systra", "https://www.systra.com/projects")
    ).extract(
        markdown,
        source_url="https://www.systra.com/en/projects/example-project/",
    )

    assert project.project_name == "Example Project"
    assert project.location_raw == "France"
    assert project.markets == ["Buildings"]
    assert project.services == ["Design"]
    assert project.description == (
        "A substantive introductory description for the example project.\n\n"
        "The remaining project narrative is retained as a second paragraph."
    )
