import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class DlrGroupExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".dlr-impact-hero__content-project-location",)
    HEADLINE_SELECTORS = (".dlr-impact-hero__content-project-name",)
    DESCRIPTION_SELECTORS = ("main p",)
    SOURCE_PATH_PATTERN = re.compile(r"/work/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".dlr-impact-hero__dataset-item")
