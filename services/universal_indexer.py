"""
Universal Data Indexer Framework
Supports multiple data sources: Obsidian, PDFs, Emails, CSVs, Text Files, etc.
"""
import asyncio
import httpx
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import mimetypes


API_URL = os.getenv("API_URL", "http://localhost:8000")
BATCH_SIZE = 10


class DataSource:
    """Base class for data source indexers"""

    def __init__(self, name: str):
        self.name = name

    async def extract_documents(self, path: str) -> List[Dict[str, Any]]:
        """Extract documents from this data source"""
        raise NotImplementedError

    def get_metadata_base(self, file_path: Path) -> Dict[str, Any]:
        """Get common file metadata"""
        stat = os.stat(file_path)
        return {
            "source": self.name,
            "file_path": str(file_path),
            "file_name": file_path.name,
            "file_size": stat.st_size,
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "mime_type": mimetypes.guess_type(file_path)[0]
        }


class TextFileIndexer(DataSource):
    """Index plain text files (.txt, .log, etc.)"""

    def __init__(self):
        super().__init__("text_file")

    async def extract_documents(self, path: str) -> List[Dict[str, Any]]:
        docs = []
        path = Path(path)

        for file_path in path.rglob("*.txt"):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                if len(content.strip()) < 20:
                    continue

                metadata = self.get_metadata_base(file_path)

                docs.append({
                    "text": content[:8000],
                    "title": file_path.stem,
                    "url": f"file://{file_path}",
                    "metadata": metadata
                })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return docs


class CSVIndexer(DataSource):
    """Index CSV files with semantic row indexing"""

    def __init__(self):
        super().__init__("csv")

    async def extract_documents(self, path: str) -> List[Dict[str, Any]]:
        docs = []
        path = Path(path)

        for file_path in path.rglob("*.csv"):
            try:
                import csv

                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)

                if not rows:
                    continue

                metadata = self.get_metadata_base(file_path)
                metadata["row_count"] = len(rows)
                metadata["columns"] = list(rows[0].keys())

                # Index file summary
                summary = f"CSV file with {len(rows)} rows and columns: {', '.join(rows[0].keys())}"

                # Add sample rows
                sample_rows = "\n".join([
                    ", ".join([f"{k}: {v}" for k, v in row.items()])
                    for row in rows[:5]
                ])

                docs.append({
                    "text": f"{summary}\n\nSample data:\n{sample_rows}",
                    "title": f"{file_path.stem} (CSV)",
                    "url": f"file://{file_path}",
                    "metadata": metadata
                })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return docs


class PDFIndexer(DataSource):
    """Index PDF files (requires PyPDF2 or pdfplumber)"""

    def __init__(self):
        super().__init__("pdf")

    async def extract_documents(self, path: str) -> List[Dict[str, Any]]:
        docs = []
        path = Path(path)

        try:
            import PyPDF2
        except ImportError:
            print("⚠️  PyPDF2 not installed. Install with: pip install PyPDF2")
            return docs

        for file_path in path.rglob("*.pdf"):
            try:
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)

                    # Extract text from all pages
                    text = ""
                    for page in pdf.pages:
                        text += page.extract_text() + "\n"

                if len(text.strip()) < 20:
                    continue

                metadata = self.get_metadata_base(file_path)
                metadata["page_count"] = len(pdf.pages)

                docs.append({
                    "text": text[:8000],
                    "title": file_path.stem,
                    "url": f"file://{file_path}",
                    "metadata": metadata
                })

            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return docs


class UniversalIndexer:
    """Main indexer that coordinates multiple data sources"""

    def __init__(self):
        self.sources = {
            "text": TextFileIndexer(),
            "csv": CSVIndexer(),
            "pdf": PDFIndexer(),
        }

    async def index_directory(
        self,
        directory: str,
        sources: List[str] = None,
        recursive: bool = True
    ):
        """Index a directory with selected data sources"""

        if sources is None:
            sources = list(self.sources.keys())

        print(f"📂 Indexing directory: {directory}")
        print(f"📋 Data sources: {', '.join(sources)}")

        all_docs = []

        # Extract documents from each source
        for source_name in sources:
            if source_name not in self.sources:
                print(f"⚠️  Unknown source: {source_name}")
                continue

            print(f"\n🔍 Extracting from {source_name}...")
            source = self.sources[source_name]
            docs = await source.extract_documents(directory)
            all_docs.extend(docs)
            print(f"   Found {len(docs)} documents")

        print(f"\n📊 Total documents to index: {len(all_docs)}")

        if not all_docs:
            print("No documents found!")
            return

        # Index in batches
        indexed = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(0, len(all_docs), BATCH_SIZE):
                batch = all_docs[i:i + BATCH_SIZE]

                try:
                    response = await client.post(
                        f"{API_URL}/index/batch",
                        json=batch
                    )
                    response.raise_for_status()
                    result = response.json()
                    indexed += result.get("indexed_count", 0)

                    print(f"Progress: {min(i + BATCH_SIZE, len(all_docs))}/{len(all_docs)} | Indexed: {indexed}")

                except Exception as e:
                    print(f"Error indexing batch: {e}")

        print(f"\n✅ Indexing complete! Indexed: {indexed} documents")


async def main():
    import sys

    if len(sys.argv) < 2:
        print("Universal Data Indexer")
        print("\nUsage: python universal_indexer.py <directory> [source_types]")
        print("\nAvailable sources:")
        print("  text  - Plain text files (.txt)")
        print("  csv   - CSV data files")
        print("  pdf   - PDF documents")
        print("\nExamples:")
        print("  python universal_indexer.py /path/to/docs")
        print("  python universal_indexer.py /path/to/data text csv")
        sys.exit(1)

    directory = sys.argv[1]
    sources = sys.argv[2:] if len(sys.argv) > 2 else None

    indexer = UniversalIndexer()
    await indexer.index_directory(directory, sources)


if __name__ == "__main__":
    asyncio.run(main())
