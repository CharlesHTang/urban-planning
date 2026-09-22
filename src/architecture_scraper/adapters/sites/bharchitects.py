import re

from ..sitemap import SitemapProjectAdapter


class BhArchitectsAdapter(SitemapProjectAdapter):
    SITE_LABEL = "B+H Architects"
    HOST = "bharchitects.com"
    LISTING_URL = "https://bharchitects.com/en/projects/"
    SITEMAP_URLS = ("https://bharchitects.com/en/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/en/project/[^/]+/?$")
