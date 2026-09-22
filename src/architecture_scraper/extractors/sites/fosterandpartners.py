import json
import re

from ..base import ProjectExtractor, clean_text
from ..html import add_fact, dedupe, html_fragment_text, split_fact_values
from ..models import ExtractedProject, FactValue


class FosterAndPartnersExtractor(ProjectExtractor):
    SOURCE_URL_PATTERN = re.compile(
        r"https://content[.]fosterandpartners[.]com/api/projects/[^/?#]+"
    )

    def extract(self, html: str, *, source_url: str) -> ExtractedProject:
        if not self.SOURCE_URL_PATTERN.fullmatch(source_url):
            raise ValueError(f"Final URL is not a project detail record: {source_url}")
        try:
            data = json.loads(html)
        except json.JSONDecodeError as error:
            raise ValueError("Foster + Partners detail record is not JSON") from error
        if not isinstance(data, dict):
            raise ValueError("Foster + Partners detail record is not an object")

        name = clean_text(str(data.get("title", "")))
        if not name:
            raise ValueError("Foster + Partners project has no title")

        description_parts = [
            html_fragment_text(str(data.get("stringdescription", "")))
        ]
        expertise = data.get("expertise")
        if isinstance(expertise, list):
            for group in expertise:
                if not isinstance(group, dict):
                    continue
                subtypes = group.get("expertiseSubtype")
                if not isinstance(subtypes, list):
                    continue
                for subtype in subtypes:
                    if isinstance(subtype, dict):
                        description_parts.append(
                            html_fragment_text(str(subtype.get("content", "")))
                        )
        descriptions = dedupe(
            value for value in description_parts if len(value) >= 40
        )
        description = "\n\n".join(descriptions) if descriptions else None

        location_data = data.get("projectLocation")
        location_parts: list[str] = []
        if isinstance(location_data, dict):
            location_parts = [
                str(location_data.get(key, ""))
                for key in ("city", "country")
                if location_data.get(key)
            ]
        location = ", ".join(dedupe(location_parts)) or None

        facts: dict[str, FactValue] = {}
        add_fact(facts, "Location", location or "")
        add_fact(facts, "Client", str(data.get("client", "")))
        project_types = self._titles(data.get("projectType"))
        add_fact(facts, "Project type", project_types)
        add_fact(facts, "Appointment year", str(data.get("appointmentYear", "")))
        add_fact(facts, "Completion date", str(data.get("completionDate", "")))
        add_fact(facts, "Project ID", str(data.get("stringprojectID", "")))

        markets = split_fact_values(facts.get("Project type"))
        warnings = [] if description else ["No substantive project description found"]
        return ExtractedProject(
            project_name=name,
            description=description,
            location_raw=location,
            client_raw=clean_text(str(data.get("client", ""))),
            status_raw=clean_text(str(data.get("completionDate", ""))),
            markets=markets,
            facts=facts,
            warnings=warnings,
        )

    @staticmethod
    def _titles(value: object) -> list[str]:
        if isinstance(value, str):
            return split_fact_values(value)
        if not isinstance(value, list):
            return []
        return dedupe(
            str(item.get("title", ""))
            for item in value
            if isinstance(item, dict)
        )
