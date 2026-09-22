import json
import re

from bs4 import BeautifulSoup

from ..base import ProjectExtractor, clean_text
from ..html import add_fact, dedupe, split_fact_values
from ..models import ExtractedProject, FactValue


class NbbjExtractor(ProjectExtractor):
    SOURCE_URL_PATTERN = re.compile(r"https://www[.]nbbj[.]com/work/[^/?#]+")
    NON_NARRATIVE_SLICES = {
        "anchor",
        "jumpnav",
        "related_content",
        "slideshow",
    }

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        if not self.SOURCE_URL_PATTERN.fullmatch(source_url):
            raise ValueError(f"Final URL is not an NBBJ project page: {source_url}")
        soup = BeautifulSoup(html, "html.parser")
        node = soup.find("script", id="__NEXT_DATA__")
        if node is None:
            raise ValueError("NBBJ project page contained no __NEXT_DATA__ record")
        try:
            payload = json.loads(node.string or node.get_text())
            page = payload["props"]["pageProps"]["page"]
            data = page["data"]
        except (KeyError, TypeError, json.JSONDecodeError) as error:
            raise ValueError("NBBJ project data was malformed") from error

        name = clean_text(str(data.get("title", "")))
        if not name:
            raise ValueError("NBBJ project has no title")

        facts: dict[str, FactValue] = {}
        add_fact(facts, "Location", str(data.get("location", "")))
        add_fact(facts, "Published date", str(data.get("published_date", "")))
        categories = self._categories(data.get("categories"))
        add_fact(facts, "Categories", categories)

        narrative: list[str] = []
        body = data.get("body")
        if isinstance(body, list):
            for section in body:
                if not isinstance(section, dict):
                    continue
                if self._project_details(section, facts):
                    continue
                if section.get("slice_type") in self.NON_NARRATIVE_SLICES:
                    continue
                narrative.extend(self._substantive_text(section))
        narrative = dedupe(narrative)
        description = "\n\n".join(narrative) if narrative else None

        services = split_fact_values(facts.get("Services"))
        warnings = [] if description else ["No substantive project description found"]
        return ExtractedProject(
            project_name=name,
            headline=clean_text(str(data.get("subtitle", ""))),
            description=description,
            location_raw=clean_text(str(data.get("location", ""))),
            client_raw=self._fact_string(facts.get("Client Name")),
            size_raw=self._fact_string(facts.get("Square Footage")),
            services=services,
            facts=facts,
            warnings=warnings,
        )

    @classmethod
    def _project_details(
        cls,
        section: dict[str, object],
        facts: dict[str, FactValue],
    ) -> bool:
        primary = section.get("primary")
        if not isinstance(primary, dict):
            return False
        is_details = primary.get("heading") == "Project Details"
        if not is_details:
            return False
        for value in primary.values():
            if not isinstance(value, list):
                continue
            entries = [item for item in value if isinstance(item, dict)]
            for index, item in enumerate(entries[:-1]):
                spans = item.get("spans")
                is_label = isinstance(spans, list) and any(
                    isinstance(span, dict)
                    and isinstance(span.get("data"), dict)
                    and span["data"].get("label") == "Definition"
                    for span in spans
                )
                if is_label:
                    add_fact(
                        facts,
                        str(item.get("text", "")),
                        str(entries[index + 1].get("text", "")),
                    )
        return True

    @classmethod
    def _substantive_text(cls, value: object) -> list[str]:
        values: list[str] = []
        if isinstance(value, dict):
            text = value.get("text")
            if isinstance(text, str) and len((clean_text(text) or "")) >= 40:
                values.append(text)
            for child in value.values():
                values.extend(cls._substantive_text(child))
        elif isinstance(value, list):
            for child in value:
                values.extend(cls._substantive_text(child))
        return values

    @staticmethod
    def _categories(value: object) -> list[str]:
        categories: list[str] = []
        if not isinstance(value, list):
            return categories
        for item in value:
            category = item.get("category") if isinstance(item, dict) else None
            if not isinstance(category, dict):
                continue
            label = category.get("data")
            if isinstance(label, dict):
                title = label.get("title")
                if isinstance(title, str):
                    categories.append(title)
                    continue
            uid = category.get("uid")
            if isinstance(uid, str):
                categories.append(uid.replace("-", " ").title())
        return dedupe(categories)

    @staticmethod
    def _fact_string(value: FactValue | None) -> str | None:
        if isinstance(value, list):
            return "; ".join(value)
        return value
