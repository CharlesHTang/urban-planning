import re

from bs4 import BeautifulSoup

from ..base import clean_text
from ..html import HtmlProjectExtractor, facts_from_containers
from ..models import ExtractedProject, FactValue


class SystraExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("h1",)
    DESCRIPTION_SELECTORS = (".entry-content.block-gut p",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/[^/]+/?")

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        if html.lstrip().startswith("---"):
            return self._extract_markdown(html, source_url=source_url)
        return super().extract(html, source_url=source_url)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        return facts_from_containers(
            soup,
            ".content-top-details .single-content",
        )

    def _extract_markdown(
        self,
        markdown: str,
        *,
        source_url: str,
    ) -> ExtractedProject:
        self._validate_source_url(source_url)
        front_matter, body = self._split_front_matter(markdown)
        title = clean_text(self._scalar(front_matter, "title"))
        if not title:
            raise ValueError("Project page has no title")

        markets = self._list(front_matter, "project-market")
        services = self._list(front_matter, "project-service")
        locations = self._list(front_matter, "project-location")
        description = self._markdown_text(body, title)
        facts: dict[str, FactValue] = {}
        if locations:
            facts["Project location"] = locations[0] if len(locations) == 1 else locations
        if markets:
            facts["Project market"] = markets[0] if len(markets) == 1 else markets
        if services:
            facts["Project service"] = services[0] if len(services) == 1 else services

        return ExtractedProject(
            project_name=title,
            description=description,
            location_raw="; ".join(locations) or None,
            services=services,
            markets=markets,
            facts=facts,
            warnings=[] if description else ["No substantive project description found"],
        )

    @staticmethod
    def _split_front_matter(markdown: str) -> tuple[list[str], str]:
        parts = markdown.lstrip().split("---", 2)
        if len(parts) != 3:
            raise ValueError("Project Markdown has invalid front matter")
        return parts[1].splitlines(), parts[2]

    @staticmethod
    def _scalar(lines: list[str], key: str) -> str | None:
        prefix = f"{key}:"
        for line in lines:
            if line.startswith(prefix):
                return line[len(prefix) :].strip().strip('"')
        return None

    @staticmethod
    def _list(lines: list[str], key: str) -> list[str]:
        values: list[str] = []
        active = False
        for line in lines:
            if line == f"{key}:":
                active = True
                continue
            if active and line.startswith("  - "):
                value = clean_text(line[4:])
                if value:
                    values.append(value)
                continue
            if active and line and not line.startswith(" "):
                break
        return values

    @staticmethod
    def _markdown_text(body: str, title: str) -> str | None:
        text = re.sub(r"!\[[^]]*]\([^)]*\)", "", body)
        text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        text = re.sub(r"[*_]{1,3}", "", text)
        paragraphs = [clean_text(value) for value in re.split(r"\n\s*\n", text)]
        values = [value for value in paragraphs if value and value != title]
        return "\n\n".join(values) or None
