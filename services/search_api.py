"""
Main search API with vector storage, semantic search, and optional Exa integration.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import httpx
import uuid
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Semantic Search API", version="1.0.0")

# CORS for canvas integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
EXA_API_KEY = os.getenv("EXA_API_KEY")
COLLECTION_NAME = "semantic_docs"
EMBEDDING_DIM = 384  # for all-MiniLM-L6-v2

# Initialize Qdrant client
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

# Models
class Document(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000)
    url: Optional[str] = ""
    title: Optional[str] = ""
    metadata: Dict[str, Any] = {}

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    filter_metadata: Optional[Dict[str, Any]] = None
    use_exa: bool = False

class SearchResult(BaseModel):
    id: str
    text: str
    url: str
    title: str
    score: float
    metadata: Dict[str, Any]

class IndexResponse(BaseModel):
    id: str
    status: str
    indexed_at: str

class StatsResponse(BaseModel):
    total_documents: int
    collection_name: str
    embedding_dimension: int

class GraphQuery(BaseModel):
    query: Optional[str] = None
    limit: int = Field(default=100, ge=10, le=300)
    similarity_threshold: float = Field(default=0.6, ge=0.3, le=0.95)
    filter_metadata: Optional[Dict[str, Any]] = None

# Startup: Create collection
@app.on_event("startup")
async def startup_event():
    try:
        # Check if collection exists
        collections = qdrant.get_collections().collections
        if COLLECTION_NAME not in [c.name for c in collections]:
            logger.info(f"Creating collection: {COLLECTION_NAME}")
            qdrant.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE
                )
            )
        else:
            logger.info(f"Collection {COLLECTION_NAME} already exists")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

# Helper: Get embeddings from service
async def get_embeddings(texts: List[str]) -> List[List[float]]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{EMBEDDING_SERVICE_URL}/embed",
                json={"text": texts}
            )
            response.raise_for_status()
            return response.json()["embeddings"]
    except Exception as e:
        logger.error(f"Embedding service error: {e}")
        raise HTTPException(status_code=503, detail="Embedding service unavailable")

# Helper: Search Exa (optional)
async def search_exa(query: str, num_results: int = 5) -> List[Dict]:
    if not EXA_API_KEY:
        return []

    try:
        from exa_py import Exa
        exa = Exa(api_key=EXA_API_KEY)

        results = exa.search_and_contents(
            query,
            num_results=num_results,
            text=True
        )

        return [
            {
                "text": r.text[:1000] if r.text else "",
                "url": r.url,
                "title": r.title or "",
                "score": 0.9,  # Exa doesn't return scores
                "metadata": {"source": "exa"}
            }
            for r in results.results
        ]
    except Exception as e:
        logger.error(f"Exa search error: {e}")
        return []

# Endpoints
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "qdrant_connected": True,
        "embedding_service": EMBEDDING_SERVICE_URL
    }

@app.post("/index", response_model=IndexResponse)
async def index_document(doc: Document):
    """Index a single document into the vector store"""
    try:
        # Generate embedding
        embeddings = await get_embeddings([doc.text])
        embedding = embeddings[0]

        # Create point
        point_id = str(uuid.uuid4())
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                "text": doc.text,
                "url": doc.url,
                "title": doc.title,
                "indexed_at": datetime.utcnow().isoformat(),
                **doc.metadata
            }
        )

        # Upsert to Qdrant
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=[point]
        )

        logger.info(f"Indexed document: {point_id}")
        return IndexResponse(
            id=point_id,
            status="indexed",
            indexed_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index/batch")
async def index_documents_batch(docs: List[Document]):
    """Index multiple documents at once"""
    try:
        texts = [doc.text for doc in docs]
        embeddings = await get_embeddings(texts)

        points = []
        ids = []
        for doc, embedding in zip(docs, embeddings):
            point_id = str(uuid.uuid4())
            ids.append(point_id)
            points.append(
                PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "text": doc.text,
                        "url": doc.url,
                        "title": doc.title,
                        "indexed_at": datetime.utcnow().isoformat(),
                        **doc.metadata
                    }
                )
            )

        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

        return {"indexed_count": len(ids), "ids": ids}

    except Exception as e:
        logger.error(f"Batch indexing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=List[SearchResult])
async def search(query: SearchQuery):
    """Semantic search over indexed documents"""
    try:
        # Get query embedding
        embeddings = await get_embeddings([query.query])
        query_embedding = embeddings[0]

        # Build filter if provided
        search_filter = None
        if query.filter_metadata:
            conditions = [
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                for key, value in query.filter_metadata.items()
            ]
            search_filter = Filter(must=conditions)

        # Search Qdrant
        results = qdrant.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_embedding,
            limit=query.limit,
            score_threshold=query.score_threshold,
            query_filter=search_filter
        )

        search_results = [
            SearchResult(
                id=str(hit.id),
                text=hit.payload.get("text", ""),
                url=hit.payload.get("url", ""),
                title=hit.payload.get("title", ""),
                score=hit.score,
                metadata={
                    k: v for k, v in hit.payload.items()
                    if k not in ["text", "url", "title"]
                }
            )
            for hit in results
        ]

        # Optionally augment with Exa
        if query.use_exa and len(search_results) < query.limit:
            exa_results = await search_exa(query.query, query.limit - len(search_results))

            # Index Exa results for future use
            if exa_results:
                for result in exa_results:
                    await index_document(Document(
                        text=result["text"],
                        url=result["url"],
                        title=result["title"],
                        metadata=result["metadata"]
                    ))

            # Add to results
            search_results.extend([
                SearchResult(
                    id=str(uuid.uuid4()),
                    **result
                )
                for result in exa_results
            ])

        return search_results

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get collection statistics"""
    try:
        collection = qdrant.get_collection(COLLECTION_NAME)
        return StatsResponse(
            total_documents=collection.points_count,
            collection_name=COLLECTION_NAME,
            embedding_dimension=EMBEDDING_DIM
        )
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document by ID"""
    try:
        qdrant.delete(
            collection_name=COLLECTION_NAME,
            points_selector=[doc_id]
        )
        return {"status": "deleted", "id": doc_id}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/graph")
async def get_semantic_graph(graph_query: GraphQuery):
    """
    Get semantic similarity graph for visualization.
    Returns nodes and edges based on embedding similarity.
    """
    try:
        # Build filter
        search_filter = None
        if graph_query.filter_metadata:
            conditions = [
                FieldCondition(
                    key=key,
                    match=MatchValue(value=value)
                )
                for key, value in graph_query.filter_metadata.items()
            ]
            search_filter = Filter(must=conditions)

        # Get documents
        if graph_query.query:
            # Search for relevant documents
            embeddings = await get_embeddings([graph_query.query])
            query_embedding = embeddings[0]

            results = qdrant.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                limit=graph_query.limit,
                query_filter=search_filter
            )

            points = [
                {
                    "id": str(hit.id),
                    "vector": hit.vector if hasattr(hit, 'vector') else None,
                    "payload": hit.payload
                }
                for hit in results
            ]
        else:
            # Get random sample of documents
            from qdrant_client.models import ScrollRequest
            scroll_result = qdrant.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=search_filter,
                limit=graph_query.limit,
                with_vectors=True
            )

            points = [
                {
                    "id": str(point.id),
                    "vector": point.vector,
                    "payload": point.payload
                }
                for point in scroll_result[0]
            ]

        # Build nodes
        nodes = []
        for point in points:
            tags = point["payload"].get("tags", [])
            nodes.append({
                "id": point["id"],
                "title": point["payload"].get("title", "Untitled"),
                "text": point["payload"].get("text", "")[:200],
                "url": point["payload"].get("url", ""),
                "tags": tags,
                "category": tags[0] if tags else "uncategorized",
                "file_path": point["payload"].get("file_path", ""),
                "vector": point["vector"]
            })

        # Build edges based on cosine similarity
        edges = []
        for i, node_a in enumerate(nodes):
            if not node_a["vector"]:
                continue

            for j, node_b in enumerate(nodes[i+1:], i+1):
                if not node_b["vector"]:
                    continue

                # Compute cosine similarity
                import numpy as np
                vec_a = np.array(node_a["vector"])
                vec_b = np.array(node_b["vector"])
                similarity = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))

                if similarity >= graph_query.similarity_threshold:
                    edges.append({
                        "source": node_a["id"],
                        "target": node_b["id"],
                        "similarity": float(similarity)
                    })

        # Remove vectors from response (too large)
        for node in nodes:
            del node["vector"]

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges)
        }

    except Exception as e:
        logger.error(f"Graph error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
