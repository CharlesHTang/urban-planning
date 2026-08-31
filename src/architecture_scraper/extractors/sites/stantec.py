import json
import re

from bs4 import BeautifulSoup, Tag

from ..html import HtmlProjectExtractor, add_fact, dedupe, text_of
from ..models import FactValue


class StantecExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ()
    TITLE_SUFFIXES = (" | Stantec",)
    SOURCE_PATH_PATTERN = re.compile(r"/en/projects/.+")

    def extract_name(self, soup: BeautifulSoup) -> str:
        name = super().extract_name(soup)
        if name.casefold() in {"project", "projects"}:
            raise ValueError("Final URL is a projects listing page")
        return name

    def extract_description(self, soup: BeautifulSoup) -> str | None:
        body = str(soup)
        parts: list[str] = []
        for match in re.finditer(
            r'"text"\s*:\s*"((?:<p>.*?</p>\s*)+)"',
            body,
            re.S,
        ):
            fragment = BeautifulSoup(match.group(1), "html.parser")
            parts.extend(text_of(node) for node in fragment.select("p"))
        values = dedupe(value for value in parts if len(value) >= 40)
        return "\n\n".join(values) if values else super().extract_description(soup)

    def extract_facts(self, soup: BeautifulSoup) -> dict[str, FactValue]:
        facts: dict[str, FactValue] = {}
        for component, data in self._templates(soup):
            if component == "ProjectInfo":
                add_fact(facts, "Location", str(data.get("location", "")))
                add_fact(facts, "Status", str(data.get("status", "")))
                clients = data.get("listClients", [])
                if isinstance(clients, list):
                    add_fact(
                        facts,
                        "Client",
                        [
                            str(item.get("clientName", ""))
                            for item in clients
                            if isinstance(item, dict)
                        ],
                    )
                for item in data.get("detailItems", []):
                    if isinstance(item, dict):
                        add_fact(
                            facts,
                            str(item.get("detailLabel", "")),
                            str(item.get("detail", "")),
                        )
            elif component == "ProjectStats":
                for item in data.get("stats", []):
                    if isinstance(item, dict):
                        add_fact(
                            facts,
                            str(item.get("statLabel", "")),
                            str(item.get("statNumber", "")),
                        )
            elif component == "ProjectTags":
                label = "Services" if data.get("tagFilter") == "service,discipline" else "Markets"
                tags = data.get("dataTags", [])
                if isinstance(tags, list):
                    add_fact(
                        facts,
                        label,
                        [
                            str(item.get("title", ""))
                            for item in tags
                            if isinstance(item, dict)
                        ],
                    )
        return facts

    @staticmethod
    def _templates(soup: BeautifulSoup) -> list[tuple[str, dict[str, object]]]:
        result: list[tuple[str, dict[str, object]]] = []
        for node in soup.find_all("template", attrs={"type": "application/json"}):
            raw = node.string or node.get_text()
            raw = re.sub(
                r"\\x([0-9a-fA-F]{2})",
                lambda match: f"\\u00{match.group(1)}",
                raw,
            )
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            mount = node.find_parent(class_="react-mount")
            if isinstance(mount, Tag):
                component = str(mount.get("data-react-component", ""))
                result.append((component, data))
        return result
