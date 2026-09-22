import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, add_fact, split_fact_values, text_of
from ..models import FactValue


class GhdExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (
        ".hero-block-complex__title",
        ".hero-block-alternate__title",
    )
    HEADLINE_SELECTORS = (".hero-block-complex__desc p",)
    DESCRIPTION_SELECTORS = (
        "main .hero-block-summary",
        "main .hero-block-complex__desc p",
        "main .content-block__description p",
        "main .content-block__description li",
        "main .content-block__description blockquote",
        "main .accordion__content p",
        "main .accordion__content li",
        "main .accordion__content blockquote",
    )
    LOCATION_SELECTORS = (
        ".hero-block-complex__subtitle",
        ".hero-block-alternate__subtitle",
    )
    TITLE_SUFFIXES = ("GHD",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/[^/]+/?")

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        parts = self.list_text(soup, self.DESCRIPTION_SELECTORS)
        if parts:
            return "\n\n".join(parts)
        return self.meta_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        for node in soup.select(".hero-block-alternate__project-details p"):
            value = text_of(node)
            if ":" not in value:
                continue
            label, content = value.split(":", 1)
            add_fact(facts, label, content)

        location = self.first_text(soup, self.LOCATION_SELECTORS)
        add_fact(facts, "Location", location or "")

        sector = facts.get("Sector") or facts.get("Sectors")
        if sector is not None:
            add_fact(facts, "Markets", split_fact_values(sector))

        add_fact(
            facts,
            "Tags",
            self.list_text(soup, ("main .tag-list .tag",)),
        )
        add_fact(
            facts,
            "Section headings",
            self.list_text(
                soup,
                (
                    "main .content-block__title",
                    "main .accordion summary",
                ),
            ),
        )
        add_fact(
            facts,
            "Image captions",
            self.list_text(soup, ("main .mosaic-figcaption",)),
        )
        return facts
