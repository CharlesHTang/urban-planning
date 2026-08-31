import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class ArupExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".projects-hero-block__details-name",)
    HEADLINE_SELECTORS = (".projects-hero-block__details-title",)
    DESCRIPTION_SELECTORS = ("#main-content .rich-text__inner p",)
    SOURCE_PATH_PATTERN = re.compile(r"/(?:[a-z]{2}-[a-z]{2}/)?projects/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".projects-detail-block__content-group")
