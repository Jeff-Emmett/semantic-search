"""
Embedding generation service using sentence-transformers.
Runs as a separate microservice to handle model loading once.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import os
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Embedding Service")

# Load model on startup
MODEL_NAME = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")
logger.info(f"Loading model: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)
logger.info(f"Model loaded. Embedding dimension: {model.get_sentence_embedding_dimension()}")

class EmbedRequest(BaseModel):
    text: str | List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dimensions: int
    model: str

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "model": MODEL_NAME,
        "dimensions": model.get_sentence_embedding_dimension()
    }

@app.post("/embed", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest):
    """Generate embeddings for one or more texts"""
    try:
        texts = [request.text] if isinstance(request.text, str) else request.text
        embeddings = model.encode(texts, convert_to_numpy=True)

        return EmbedResponse(
            embeddings=embeddings.tolist(),
            dimensions=model.get_sentence_embedding_dimension(),
            model=MODEL_NAME
        )
    except Exception as e:
        logger.error(f"Embedding error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
