import requests
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree
from loguru import logger


def find_sitemap_from_robots(base_url: str) -> list[str]:
    """
    Check robots.txt for sitemap declarations.
    
    Args:
        base_url: Base domain URL
    
    Returns:
        List of sitemap URLs found in robots.txt
    """
    robots_url = urljoin(base_url, "/robots.txt")
    sitemaps = []
    
    try:
        logger.debug(f"Checking robots.txt at: {robots_url}")
        r = requests.get(robots_url, timeout=10)
        r.raise_for_status()
        
        for line in r.text.splitlines():
            line = line.strip()
            if line.lower().startswith("sitemap:"):
                sitemap_url = line.split(":", 1)[1].strip()
                sitemaps.append(sitemap_url)
                logger.info(f"Found sitemap in robots.txt: {sitemap_url}")
    except Exception as exc:
        logger.debug(f"Could not fetch robots.txt: {exc}")
    
    return sitemaps


def try_fetch_sitemap(sitemap_url: str) -> ElementTree.Element | None:
    """
    Try to fetch and parse a sitemap from given URL.
    
    Args:
        sitemap_url: Full URL to sitemap
    
    Returns:
        Parsed XML root element or None if failed
    """
    try:
        logger.debug(f"Trying sitemap URL: {sitemap_url}")
        r = requests.get(sitemap_url, timeout=10)
        r.raise_for_status()
        
        # Try to parse as XML
        root = ElementTree.fromstring(r.content)
        logger.success(f"Successfully fetched sitemap: {sitemap_url}")
        return root
    except ElementTree.ParseError as exc:
        logger.debug(f"XML parse error for {sitemap_url}: {exc}")
    except requests.exceptions.RequestException as exc:
        logger.debug(f"Request failed for {sitemap_url}: {exc}")
    except Exception as exc:
        logger.debug(f"Unexpected error for {sitemap_url}: {exc}")
    
    return None


def extract_urls_from_sitemap(root: ElementTree.Element, sitemap_url: str, visited: set) -> set[str]:
    """
    Extract URLs from a sitemap XML element.
    Handles both sitemap indexes and regular sitemaps.
    
    Args:
        root: XML root element
        sitemap_url: URL of the sitemap being processed
        visited: Set of already visited sitemap URLs
    
    Returns:
        Set of URLs found
    """
    urls = set()
    ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    
    # Check if it's a sitemap index (contains other sitemaps)
    if root.tag.endswith("sitemapindex"):
        logger.info(f"Found sitemap index at {sitemap_url}")
        for loc in root.findall(".//ns:loc", ns):
            sm_url = loc.text.strip()
            if sm_url not in visited:
                visited.add(sm_url)
                logger.debug(f"Following sitemap index entry: {sm_url}")
                urls |= fetch_all_sitemap_urls(sm_url, visited)
    else:
        # Regular sitemap with URLs
        found_urls = root.findall(".//ns:loc", ns)
        if found_urls:
            logger.info(f"Found {len(found_urls)} URLs in sitemap: {sitemap_url}")
            for loc in found_urls:
                urls.add(loc.text.strip())
        else:
            # Try without namespace (some sitemaps don't use it)
            found_urls_no_ns = root.findall(".//loc")
            if found_urls_no_ns:
                logger.info(f"Found {len(found_urls_no_ns)} URLs in sitemap (no namespace): {sitemap_url}")
                for loc in found_urls_no_ns:
                    urls.add(loc.text.strip())
    
    return urls


def fetch_all_sitemap_urls(base_url: str, visited=None) -> set[str]:
    """
    Fetch all URLs from sitemap(s) for a given domain.
    Tries multiple common sitemap locations and checks robots.txt.
    
    Args:
        base_url: Base domain URL (e.g., https://example.com)
        visited: Set of already visited sitemap URLs (used for recursion)
    
    Returns:
        Set of all URLs found in sitemaps
    """
    if visited is None:
        visited = set()
        logger.info(f"Starting sitemap discovery for: {base_url}")
    
    urls = set()
    
    # Common sitemap locations to try (in order of preference)
    sitemap_paths = [
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap",
        "/sitemap.php",
        "/sitemap.txt",
        "/sitemap1.xml",
    ]
    
    # First, check robots.txt for sitemap declarations
    if not visited:  # Only check robots.txt on first call, not during recursion
        robots_sitemaps = find_sitemap_from_robots(base_url)
        for sitemap_url in robots_sitemaps:
            if sitemap_url not in visited:
                visited.add(sitemap_url)
                root = try_fetch_sitemap(sitemap_url)
                if root is not None:
                    urls |= extract_urls_from_sitemap(root, sitemap_url, visited)
                    if urls:
                        logger.success(f"Found {len(urls)} total URLs from sitemap discovery")
                        return urls  # Success, return immediately
    
    # Try common sitemap locations
    for path in sitemap_paths:
        sitemap_url = urljoin(base_url, path)
        
        if sitemap_url in visited:
            continue
        
        visited.add(sitemap_url)
        root = try_fetch_sitemap(sitemap_url)
        
        if root is not None:
            urls |= extract_urls_from_sitemap(root, sitemap_url, visited)
            if urls:
                logger.success(f"Found {len(urls)} total URLs from sitemap discovery")
                return urls  # Success, return immediately
    
    if not urls:
        logger.warning(f"No sitemap found for {base_url}")
    
    return urls