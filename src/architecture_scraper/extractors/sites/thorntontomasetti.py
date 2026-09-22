import re

from bs4 import BeautifulSoup

from ..html import (
    HtmlProjectExtractor,
    add_fact,
    fact_value_raw,
    facts_from_containers,
    split_fact_values,
)
from ..models import FactValue


class ThorntonTomasettiExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("article.node--type-project h1",)
    HEADLINE_SELECTORS = (".field--field_project_summary",)
    DESCRIPTION_SELECTORS = (
        "article.node--type-project .field--field_body p",
        "article.node--type-project .field--field_body li",
        "article.node--type-project .field--field_body blockquote",
    )
    SERVICES_SELECTORS = (
        "article.node--type-project "
        ".field--name-field-capabilities .views-field-name",
    )
    MARKETS_SELECTORS = (
        "article.node--type-project "
        ".related-solutions .field--field_short_title",
    )
    TITLE_SUFFIXES = ("Thornton Tomasetti",)
    SOURCE_PATH_PATTERN = re.compile(r"/project/[^/]+/?")

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        parts = self.list_text(soup, self.DESCRIPTION_SELECTORS)
        if parts:
            return "\n\n".join(parts)
        return self.meta_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        article = soup.select_one("article.node--type-project")
        if article is None:
            return {}

        facts = facts_from_containers(article, ".details .detail")
        owner = fact_value_raw(facts, "owner")
        if owner is not None:
            add_fact(facts, "Client", split_fact_values(owner))

        add_fact(
            facts,
            "Project Awards",
            self.list_text(article, (".details .awards p",)),
        )
        add_fact(
            facts,
            "Lead contacts",
            self.list_text(article, (".project-person .name",)),
        )
        add_fact(
            facts,
            "Capabilities",
            self.list_text(article, self.SERVICES_SELECTORS),
        )
        add_fact(
            facts,
            "Related solutions",
            self.list_text(article, self.MARKETS_SELECTORS),
        )
        add_fact(
            facts,
            "Image captions",
            self.list_text(article, (".field--field_photo_caption_1",)),
        )
        add_fact(
            facts,
            "Image credits",
            self.list_text(article, (".field--field_photo_credit",)),
        )
        return facts
