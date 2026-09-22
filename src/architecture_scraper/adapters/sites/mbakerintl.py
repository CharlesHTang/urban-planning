import re

from ..sitemap import SitemapProjectAdapter


class MBakerIntlAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Michael Baker International"
    HOST = "mbakerintl.com"
    LISTING_URL = "https://mbakerintl.com/projects/"
    SITEMAP_URLS = ("https://mbakerintl.com/projects-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
