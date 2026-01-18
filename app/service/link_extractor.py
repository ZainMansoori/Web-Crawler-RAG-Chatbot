from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def extract_internal_links(html: str, base_url: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc

    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        # skip junk
        if href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue

        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc != base_domain:
            continue  # external link

        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
        links.add(normalized)

    return links
