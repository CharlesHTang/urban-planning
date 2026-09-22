import re

from ..sitemap import SitemapProjectAdapter


class ImegAdapter(SitemapProjectAdapter):
    SITE_LABEL = "IMEG"
    HOST = "imegcorp.com"
    LISTING_URL = "https://imegcorp.com/projects/"
    SITEMAP_URLS = (
        "https://imegcorp.com/project-sitemap.xml",
        "https://imegcorp.com/project-sitemap2.xml",
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/project/[^/]+/?$")
