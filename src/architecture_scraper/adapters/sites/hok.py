import re

from ..sitemap import SitemapProjectAdapter


class HokAdapter(SitemapProjectAdapter):
    SITE_LABEL = "HOK"
    HOST = "www.hok.com"
    SITEMAP_URLS = (
        "https://www.hok.com/projects-sitemap1.xml",
        "https://www.hok.com/projects-sitemap2.xml",
    )
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/view/[^/]+/?$")
