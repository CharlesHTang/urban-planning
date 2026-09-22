import re

from bs4 import BeautifulSoup

from ..base import clean_text
from ..html import HtmlProjectExtractor, add_fact, fact_value_raw, text_of
from ..models import FactValue


class NikkenExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".c-project-pageHeader__hdg",)
    HEADLINE_SELECTORS = (".p-projectsDet__detail__hdg",)
    DESCRIPTION_SELECTORS = (".l-article-col__main .lead",)
    # The header occasionally contains translation artifacts such as
    # "Gifu, , Japan"; the project table contains the clean location.
    LOCATION_SELECTORS = ()
    SERVICES_SELECTORS = (
        '.l-article-info a[href*="/services/"]',
    )
    MARKETS_SELECTORS = (
        '.l-article-info a[href*="domain_id"]',
    )
    TITLE_SUFFIXES = ("PROJECTS | NIKKEN SEKKEI LTD",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/(?:[^/]+/)*[^/]+\.html")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        for row in soup.select(".l-article-col__main table tr"):
            label = text_of(row.select_one("th"))
            value = text_of(row.select_one("td"))
            add_fact(facts, label, value)

        for container in soup.select(".l-article-info"):
            label = text_of(container.select_one(".l-article-info__title"))
            values = self.list_text(
                container,
                ("li",),
            )
            add_fact(facts, label, values)

        add_fact(
            facts,
            "Photo credits",
            self.list_text(
                soup,
                (".c-carousel-02__item",),
            ),
        )
        add_fact(
            facts,
            "Project people",
            self.list_text(
                soup,
                (".c-lyt-col--people .c-lyt-col__item",),
            ),
        )

        client = self._first_fact(
            facts,
            "client",
            "architect",
            "owner",
            "建築主",
            "业主",
        )
        if client is not None:
            add_fact(facts, "Client", client)

        location = self._first_fact(facts, "location", "所在地")
        if location is None:
            header_location = self.first_text(
                soup,
                (".c-project-pageHeader__text",),
            )
            location = clean_text(
                re.sub(r",\s*,", ",", header_location or "")
            )
        if location is not None:
            add_fact(facts, "Location", location)

        status = self._first_fact(
            facts,
            "completion",
            "planned completion",
            "completion date",
            "project completion year",
            "プロジェクト完了年",
            "竣工年",
            "竣工",
        )
        if status is not None:
            add_fact(facts, "Status", status)

        size = self._first_fact(
            facts,
            "total floor area",
            "延べ面積",
            "建筑面积",
            "site area",
            "敷地面積",
        )
        if size is not None:
            add_fact(facts, "Size", size)
        return facts

    @staticmethod
    def _first_fact(
        facts: dict[str, FactValue],
        *labels: str,
    ) -> FactValue | None:
        for label in labels:
            value = fact_value_raw(facts, label)
            if value is not None:
                return value
        return None
