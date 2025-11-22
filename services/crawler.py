"""
Simple web crawler for building initial corpus.
Usage: python crawler.py <start_url>
"""
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List, Tuple
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_URL = "http://localhost:8000"

async def crawl_and_index(
    start_url: str,
    max_depth: int = 2,
    max_pages: int = 100,
    same_domain_only: bool = True
):
    """Crawl website and index content"""
    visited: Set[str] = set()
    to_visit: List[Tuple[str, int]] = [(start_url, 0)]
    start_domain = urlparse(start_url).netloc

    async with httpx.AsyncClient(timeout=30.0) as client:
        while to_visit and len(visited) < max_pages:
            url, depth = to_visit.pop(0)

            if url in visited or depth > max_depth:
                continue

            try:
                logger.info(f"Crawling: {url} (depth: {depth})")
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
                visited.add(url)

                soup = BeautifulSoup(resp.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                title = soup.title.string if soup.title else url

                # Index if substantial content
                if len(text) > 100:
                    logger.info(f"Indexing: {title[:50]}...")
                    await client.post(
                        f"{API_URL}/index",
                        json={
                            "text": text[:5000],  # Chunk long documents
                            "url": url,
                            "title": title,
                            "metadata": {
                                "depth": depth,
                                "crawled_at": "2024-11-22"
                            }
                        }
                    )

                # Find links for next depth
                if depth < max_depth:
                    for link in soup.find_all('a', href=True):
                        next_url = urljoin(url, link['href'])
                        next_domain = urlparse(next_url).netloc

                        # Filter by domain if required
                        if same_domain_only and next_domain != start_domain:
                            continue

                        # Skip non-http(s) URLs
                        if not next_url.startswith(('http://', 'https://')):
                            continue

                        if next_url not in visited:
                            to_visit.append((next_url, depth + 1))

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                continue

    logger.info(f"Crawl complete. Visited {len(visited)} pages.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python crawler.py <start_url> [max_depth] [max_pages]")
        sys.exit(1)

    url = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    asyncio.run(crawl_and_index(url, max_depth=depth, max_pages=pages))
