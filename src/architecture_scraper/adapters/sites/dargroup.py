import re

from ..sitemap import SitemapProjectAdapter


class DarGroupAdapter(SitemapProjectAdapter):
    """Discover projects from Dar Group's renamed Sidara website."""

    SITE_LABEL = "Dar Group / Sidara"
    HOST = "sidaracollaborative.com"
    LISTING_URL = "https://sidaracollaborative.com/en/projects"
    SITEMAP_URLS = ("https://sidaracollaborative.com/sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
    EXCLUDED_PROJECT_PATHS = frozenset({"/projects", "/projects/"})
