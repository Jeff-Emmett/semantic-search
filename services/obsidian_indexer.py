"""
Obsidian Vault Indexer - Index all markdown files from an Obsidian vault
Extracts frontmatter, tags, links, and content for semantic search
"""
import asyncio
import httpx
import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import yaml


API_URL = os.getenv("API_URL", "http://localhost:8000")
BATCH_SIZE = 10  # Index 10 documents at a time


def extract_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from markdown content"""
    frontmatter = {}
    body = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, body


def extract_obsidian_tags(content: str) -> List[str]:
    """Extract #tags from content"""
    # Match #tag but not ##heading or #tag-with-dash
    tags = re.findall(r'(?:^|\s)#([a-zA-Z][a-zA-Z0-9/_-]*)', content)
    return list(set(tags))


def extract_wikilinks(content: str) -> List[str]:
    """Extract [[wikilinks]] from content"""
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    # Handle [[link|alias]] format
    links = [link.split('|')[0].strip() for link in links]
    return list(set(links))


def clean_content(content: str) -> str:
    """Clean markdown content for indexing"""
    # Remove excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    # Remove empty list items
    content = re.sub(r'^\s*[-*]\s*$', '', content, flags=re.MULTILINE)
    return content.strip()


async def index_file(
    client: httpx.AsyncClient,
    file_path: Path,
    vault_path: Path
) -> Optional[Dict]:
    """Index a single markdown file"""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip empty files
        if not content.strip():
            return None

        # Extract components
        frontmatter, body = extract_frontmatter(content)
        tags = extract_obsidian_tags(body)
        links = extract_wikilinks(body)
        body_clean = clean_content(body)

        # Skip if no meaningful content (lowered threshold to capture short notes)
        if len(body_clean) < 1:
            return None

        # Get file metadata
        stat = os.stat(file_path)
        relative_path = str(file_path.relative_to(vault_path))

        # Convert datetime objects in frontmatter to ISO strings
        serializable_frontmatter = {}
        for key, value in frontmatter.items():
            if isinstance(value, datetime):
                serializable_frontmatter[key] = value.isoformat()
            else:
                serializable_frontmatter[key] = value

        # Build metadata
        metadata = {
            "source": "obsidian",
            "file_path": relative_path,
            "file_name": file_path.name,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "size_bytes": stat.st_size,
            "tags": tags,
            "links": links[:10],  # Limit to first 10 links
            "link_count": len(links),
            **serializable_frontmatter  # Include all frontmatter fields
        }

        # Create document
        doc = {
            "text": body_clean[:8000],  # Limit to 8000 chars for embedding
            "title": file_path.stem,
            "url": f"obsidian://open?vault=Jeff's Vault&file={relative_path}",
            "metadata": metadata
        }

        return doc

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


async def index_vault(vault_path: str, skip_hidden: bool = True):
    """Index entire Obsidian vault"""
    vault_path = Path(vault_path)

    # Find all markdown files
    print(f"📚 Scanning vault: {vault_path}")
    md_files = []
    for md_file in vault_path.rglob("*.md"):
        # Skip hidden folders
        if skip_hidden and any(part.startswith('.') for part in md_file.parts):
            continue
        md_files.append(md_file)

    print(f"Found {len(md_files)} markdown files")

    # Process files
    indexed = 0
    skipped = 0
    errors = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Process in batches
        for i in range(0, len(md_files), BATCH_SIZE):
            batch = md_files[i:i + BATCH_SIZE]

            # Parse files
            docs = []
            for file_path in batch:
                doc = await index_file(client, file_path, vault_path)
                if doc:
                    docs.append(doc)
                else:
                    skipped += 1

            # Index batch
            if docs:
                try:
                    response = await client.post(
                        f"{API_URL}/index/batch",
                        json=docs
                    )
                    response.raise_for_status()
                    result = response.json()
                    indexed += result.get("indexed_count", 0)

                    # Progress update
                    progress = min(i + BATCH_SIZE, len(md_files))
                    print(f"Progress: {progress}/{len(md_files)} files | "
                          f"Indexed: {indexed} | Skipped: {skipped}")

                except Exception as e:
                    print(f"Error indexing batch: {e}")
                    errors += len(docs)

    print(f"\n✅ Indexing complete!")
    print(f"   📝 Indexed: {indexed}")
    print(f"   ⏭️  Skipped: {skipped} (empty/short)")
    print(f"   ❌ Errors: {errors}")

    # Get final stats
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_URL}/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"\n📊 Collection Stats:")
                print(f"   Total documents: {stats.get('total_documents', 'N/A')}")
        except:
            pass


async def search_vault(query: str, limit: int = 10):
    """Search the indexed vault"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_URL}/search",
            json={
                "query": query,
                "limit": limit,
                "score_threshold": 0.3,
                "filter_metadata": {"source": "obsidian"}
            }
        )
        results = response.json()

        print(f"\n🔍 Search: '{query}'")
        print(f"Found {len(results)} results:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']} (score: {result['score']:.3f})")
            print(f"   Path: {result['metadata'].get('file_path', 'N/A')}")
            print(f"   Tags: {', '.join(result['metadata'].get('tags', []))}")
            print(f"   Preview: {result['text'][:100]}...")
            print(f"   URL: {result['url']}\n")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  Index vault:  python obsidian_indexer.py index <vault_path>")
        print("  Search vault: python obsidian_indexer.py search <query>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "index":
        if len(sys.argv) < 3:
            print("Please provide vault path")
            sys.exit(1)
        vault_path = sys.argv[2]
        asyncio.run(index_vault(vault_path))

    elif command == "search":
        if len(sys.argv) < 3:
            print("Please provide search query")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        asyncio.run(search_vault(query))

    else:
        print(f"Unknown command: {command}")
        print("Use 'index' or 'search'")
