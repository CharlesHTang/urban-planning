import re

from ..sitemap import SitemapProjectAdapter


class BuroHappoldAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Buro Happold"
    HOST = "www.burohappold.com"
    SITEMAP_INDEX_URL = "https://www.burohappold.com/sitemap_index.xml"
    SITEMAP_URL_PATTERN = re.compile(
        r"^https://www\.burohappold\.com/projects-sitemap\d*\.xml$"
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
    EXCLUDED_PROJECT_PATHS = frozenset({"/projects", "/projects/"})
