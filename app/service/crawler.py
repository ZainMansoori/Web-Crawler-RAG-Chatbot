import requests

def fetch_html(url: str) -> str:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.text
