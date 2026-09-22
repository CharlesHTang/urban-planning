import re

from ..sitemap import SitemapProjectAdapter


class DpaAdapter(SitemapProjectAdapter):
    SITE_LABEL = "DP Architects"
    HOST = "www.dpa.com.sg"
    SITEMAP_URLS = ("https://www.dpa.com.sg/projects-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
