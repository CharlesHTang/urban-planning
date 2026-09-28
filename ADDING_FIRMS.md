# Adding a firm: download adapter and text extractor

The projects-page URL is the starting point. A **download adapter** discovers
the firm's project detail URLs and saves each complete response. A separate
**extractor** reads those saved responses and turns each project into one
structured JSON record. Both are selected by the firm's entry in `sites.yml`.

Work from the repository root. If this is a fresh checkout, install the package
first:

```bash
python -m venv venv
venv/bin/pip install -e '.[test]'
venv/bin/playwright install chromium
```

## 1. Inspect how the firm publishes projects

Open the known projects page. Determine where the *detail page URLs* come from:

- A project sitemap: check the site's `robots.txt` or sitemap index. Confirm the
  entries are actual project detail pages, not articles or listing pages.
- HTML links: inspect the listing page and its pagination, “show more” button,
  or infinite scrolling. Check whether the links are present in the initial
  HTML or appear only after browser interaction.
- A JSON API: in browser DevTools, open **Network**, filter to **Fetch/XHR**,
  reload the page, and use pagination or “show more.” Inspect the response,
  request parameters, page size, total count, and project URL field.

Use the simplest reliable source that covers the site's whole project set. In
particular, check that pagination reaches the last page, and reject unrelated
URLs. A listing that looks complete in the browser may contain only the first
batch of projects.

## 2. Add the download adapter

Create `src/architecture_scraper/adapters/sites/example.py`. For a firm with a
project sitemap, the adapter can be very small:

```python
import re

from ..sitemap import SitemapProjectAdapter


class ExampleAdapter(SitemapProjectAdapter):
    SITE_LABEL = "Example"
    HOST = "www.example.com"
    SITEMAP_URLS = ("https://www.example.com/project-sitemap.xml",)
    PROJECT_PATH_PATTERN = re.compile(r"^/projects/[^/]+/?$")
```

`SitemapProjectAdapter` fetches the listing and sitemap, keeps only matching
HTTPS URLs on `HOST`, and returns the discovered detail URLs. If the sitemap is
part of a sitemap index, see `SITEMAP_INDEX_URL` and `SITEMAP_URL_PATTERN` in
`src/architecture_scraper/adapters/sitemap.py`. See the SYSTRA or IMEG adapter
for concrete examples. Match the site's *actual* detail path; a broad pattern
can accidentally include navigation pages.

If links come from listing HTML, subclass `SiteAdapter` and implement
`discover(fetcher)`. Fetch the known listing URL, keep its response as a
listing snapshot, and return `DiscoveryResult(listing_pages, project_urls)`.
For ordinary links, the shape is:

```python
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ...fetcher import Fetcher
from ...models import DiscoveryResult
from ..base import SiteAdapter


class ExampleAdapter(SiteAdapter):
    async def discover(self, fetcher: Fetcher) -> DiscoveryResult:
        response = await fetcher.fetch(
            self.config.projects_url,
            render=self.config.listing_render,
        )
        listing = self.listing_from_fetch(response)
        soup = BeautifulSoup(response.html, "html.parser")
        urls = []
        for link in soup.select("a[href]"):
            url = urljoin(response.url, link["href"])
            parsed = urlparse(url)
            if (
                parsed.scheme == "https"
                and parsed.netloc == "www.example.com"
                and parsed.path.startswith("/projects/")
            ):
                urls.append(url)
        return DiscoveryResult([listing], urls)
```

Adapt the selector and URL checks to the site. Exclude the listing itself,
query variants, and paths that are not detail pages. If there are multiple
listing pages, fetch each and include each snapshot in `listing_pages`. For
“show more” or infinite scroll, use `fetcher.browser_page(...)`, interact with
the Playwright page, and call `await self.listing_from_page(page)` after the
content loads. See `src/architecture_scraper/adapters/base.py` for both listing
helpers. If a public API exposes all project URLs, paginate it in `discover`;
`fetcher.fetch(...)` handles GET and `fetcher.post_json(...)` handles JSON POST.
The AECOM and Arcadis adapters show each pattern.

The adapter should return detail URLs; the shared `CollectionRunner` handles
URL normalization, duplicate URLs, request pacing, fetching, raw storage, and
errors. Override `fetch_detail(...)` only when the site needs special detail
requests. `render="never"` uses `curl_cffi`; `render="always"` uses Playwright;
`render="auto"` tries HTTP first and falls back to Playwright.

## 3. Register the firm in `sites.yml`

Add one entry, using a unique short name consistently for the output folders:

```yaml
  - name: example
    projects_url: https://www.example.com/projects
    adapter: architecture_scraper.adapters.sites.example:ExampleAdapter
    extractor: architecture_scraper.extractors.sites.example:ExampleExtractor
    listing_render: never
    detail_render: never
    concurrency: 5
    request_delay: 0.5
    timeout: 90
    impersonate: chrome
```

The import references use `module:ClassName`. Adjust the request delay and
concurrency for the site's behavior and crawl guidance. Change the render mode
only when needed; some sites require a different `curl_cffi` impersonation
profile. The `extractor` reference can be added after downloading if you want
to inspect raw pages first. There are no selectors in YAML.

## 4. Download and verify raw pages

Run one firm at a time:

```bash
venv/bin/architecture-scraper collect sites.yml --site example -o raw-pages --resume
```

`collect` rediscovers URLs on every run, writes
`raw-pages/example/project_urls.txt`, saves listing snapshots under
`raw-pages/example/listing/`, and saves detail responses under
`raw-pages/example/detail/`. `raw-pages/manifest.jsonl` records the requested
URL, final URL, file path, and capture time. The `.html` filenames are hashes
of the requested URLs, so use the manifest to map files back to projects.
An API response may contain JSON even though its raw filename ends in `.html`.

With `--resume`, existing non-empty detail files are skipped and missing or
empty ones are fetched. Omit it to deliberately refresh all detail responses.
Each successful page is written atomically. The listing may still be fetched
again during resume because discovery runs again.

Before extraction, compare the URL count with the saved detail count and
inspect a few files from the start, middle, and end of the URL list. Check that
they contain the project's actual name, description, and facts rather than a
login, error, challenge, or truncated preview. Review any failures printed by
`collect`; some URLs may redirect to non-project pages. If an API or sitemap
reports a total, compare that total with the discovered URL count. A zero-error
run alone does not prove that discovery found every project.

If you already have a checked list of detail URLs, you can skip adapter
discovery and run:

```bash
venv/bin/architecture-scraper fetch-details \
  sites.yml example example-project-urls.txt -o raw-pages --resume
```

## 5. Add the extractor

Create `src/architecture_scraper/extractors/sites/example.py`. For normal HTML,
start with `HtmlProjectExtractor` and selectors based on the *downloaded detail
HTML*, not just what the browser renders:

```python
import re

from ..html import HtmlProjectExtractor


class ExampleExtractor(HtmlProjectExtractor):
    NAME_SELECTORS = ("main h1",)
    DESCRIPTION_SELECTORS = ("main .project-body p",)
    LOCATION_SELECTORS = ("main .project-location",)
    SOURCE_PATH_PATTERN = re.compile(r"/projects/[^/]+/?")
```

The shared extractor fills the `ExtractedProject` fields: `project_name`,
`headline`, `description`, `location_raw`, `client_raw`, `status_raw`,
`size_raw`, `services`, `markets`, `facts`, and `warnings`. Only the name is
required. It joins substantive description paragraphs, removes duplicates,
and can fall back to a meta description. Check that the result contains the
*full* narrative; a meta description may be just a short summary.

Add selectors for other fields only where the source provides them. For
label/value facts, override `extract_facts(soup)` and use helpers such as
`facts_from_definition_lists`, `facts_from_containers`, or `add_fact` in
`src/architecture_scraper/extractors/html.py`. Keep unknown values as `None`
or empty lists instead of guessing. `SOURCE_PATH_PATTERN` validates the
**final** URL after redirects; allow legitimate project language/host variants
and reject non-project destinations.

If the detail response is JSON or another format, subclass `ProjectExtractor`
and implement `extract(html, *, source_url)` returning an `ExtractedProject`.
The Foster + Partners extractor is an example: it parses a JSON API record
stored in the raw file. The SYSTRA extractor shows how to handle a site that
sometimes returns Markdown. Bump the extractor's `VERSION` when you change its
output logic so the stored records identify which implementation produced them.

## 6. Use AI to add a firm

Give the AI coding assistant access to this repository and replace
`<firm-name>`, `<site-name>`, and `<projects-page-url>` in the prompts below.
Use the short `sites.yml` name for `<site-name>` (for example, `imeg`). Work
through the prompts in order: the extractor needs real downloaded detail pages
as evidence, so it comes after discovery and collection.

### Prompt 1: Find the project URL source

```text
I want to add <firm-name> to this architecture-scraper repository.
The known projects page is <projects-page-url>.

First inspect the existing adapters, sites.yml, and the site's public
projects page. Find how to enumerate ALL project detail URLs. Check for a
project sitemap or sitemap index, ordinary listing pagination, and the
Fetch/XHR requests used by show-more buttons or infinite scroll. If you
find an API, give its exact endpoint, method, required parameters or POST
body, pagination rule, total-count field, and project URL field. Show the
actual response evidence and a few example detail URLs. Compare the
discovered count with any total the site publishes, and identify non-project
URLs or redirects that must be excluded. Recommend the simplest reliable
discovery method. Do not write code yet or invent an endpoint you cannot
verify. If you cannot inspect the network requests, tell me exactly what
to capture in Chrome DevTools so I can provide it.
```

### Prompt 2: Write and test the download adapter

```text
Using the discovery method you verified for <firm-name>, implement its
download adapter in src/architecture_scraper/adapters/sites/ and add
<site-name> to sites.yml. Follow the existing SiteAdapter or
SitemapProjectAdapter conventions. My starting URL is
<projects-page-url>; I do not know the detail URLs. Make the adapter
discover all detail URLs, handle every page of pagination, filter out
non-project URLs, and save the full raw detail responses through the
existing CollectionRunner. Use curl_cffi for ordinary requests and
Playwright only when this site needs browser interaction. Add a focused
adapter test with representative sitemap, HTML, or API data. Run that
test and a small live discovery check. Report the discovered count and
any uncertainty before starting a large download.
```

After reviewing the count, run the site alone with `--resume`:

```bash
venv/bin/architecture-scraper collect sites.yml --site <site-name> -o raw-pages --resume
```

### Prompt 3: Write, run, and verify the extractor

```text
Using the downloaded <site-name> detail files in raw-pages/ and their
manifest entries, implement a site extractor in
src/architecture_scraper/extractors/sites/. Inspect several different
project layouts before choosing selectors or JSON fields. Return the
shared ExtractedProject fields, preserving the full project narrative
and every useful labeled fact actually present in the source. Do not
guess missing values or use a short meta description when a longer
body exists. Register the extractor in sites.yml and add focused tests
using representative raw responses. Run the tests to verify the extractor.
```

Run the extraction with

```bash
venv/bin/architecture-scraper extract sites.yml --site <site-name> --raw raw-pages -o extracted
```