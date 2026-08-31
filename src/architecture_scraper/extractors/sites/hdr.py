import re

from bs4 import BeautifulSoup

from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import FactValue


class HdrExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = (".project-node__page-title",)
    HEADLINE_SELECTORS = (".field--name-body h2",)
    DESCRIPTION_SELECTORS = ("article.project-node .field--name-body p",)
    SERVICES_SELECTORS = (".field--name-field-services .field__item a",)
    MARKETS_SELECTORS = (".field--name-field-markets .field__item a",)
    SOURCE_PATH_PATTERN = re.compile(r"/portfolio/[^/]+/?")

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(soup, ".project-node__sidebar > .field")
