from collections import deque
from loguru import logger
from app.service.crawler import fetch_html
from app.service.link_extractor import extract_internal_links

def crawl_domain(start_url: str, max_pages: int = 100):
    visited = set()
    queue = deque([start_url])

    while queue and len(visited) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue

        try:
            html = fetch_html(url)
        except Exception as exc:
            logger.warning(f"Failed to fetch {url}: {exc}")
            continue

        visited.add(url)
        yield url, html

        links = extract_internal_links(html, url)
        for link in links:
            if link not in visited:
                queue.append(link)
