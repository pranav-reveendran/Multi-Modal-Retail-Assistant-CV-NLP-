"""
FastAPI Backend for Multi-Modal Retail Assistant
Provides REST API endpoints for image and text search
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
from PIL import Image
import io
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.search_engine import SearchEngine


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Modal Retail Assistant API",
    description="Search for products using images or text queries powered by CLIP",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global search engine instance
search_engine = None


# Request/Response models
class TextSearchRequest(BaseModel):
    query: str
    k: int = 5
    search_mode: str = "text"  # "text" or "hybrid"


class SearchResult(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    brand: Optional[str] = None
    price: float
    image_path: str
    similarity_score: float
    distance: float


class SearchResponse(BaseModel):
    query_type: str
    results: List[SearchResult]
    num_results: int


@app.on_event("startup")
async def startup_event():
    """Initialize search engine on startup"""
    global search_engine

    # Get paths from environment variables or use defaults
    vector_db_path = os.getenv("VECTOR_DB_PATH", "data/vector_db")
    model_name = os.getenv("CLIP_MODEL_NAME", "clip-ViT-B-32")

    print(f"Initializing search engine...")
    print(f"  - Vector DB path: {vector_db_path}")
    print(f"  - CLIP model: {model_name}")

    try:
        search_engine = SearchEngine(
            vector_db_path=vector_db_path,
            model_name=model_name
        )
        print("✅ Search engine initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing search engine: {e}")
        print("Make sure to run the setup scripts first:")
        print("  1. python scripts/download_dataset.py")
        print("  2. python scripts/build_embeddings.py")
        print("  3. python scripts/build_vector_db.py")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Multi-Modal Retail Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "search_image": "/search/image",
            "search_text": "/search/text",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Health check with system status"""
    if search_engine is None:
        return {
            "status": "error",
            "message": "Search engine not initialized"
        }

    return {
        "status": "healthy",
        "search_engine": "ready",
        "num_products": len(search_engine.vector_db.metadata) if search_engine.vector_db else 0
    }


@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    k: int = 5,
    search_mode: str = "image"
):
    """
    Search for similar products using an uploaded image

    Args:
        file: Uploaded image file
        k: Number of results to return
        search_mode: "image" for image similarity, "hybrid" for cross-modal search

    Returns:
        SearchResponse with similar products
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Search
        results = search_engine.search_by_image(image, k=k, search_mode=search_mode)

        return SearchResponse(
            query_type="image",
            results=[SearchResult(**r) for r in results],
            num_results=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image search: {str(e)}")


@app.post("/search/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Search for similar products using a text query

    Args:
        request: TextSearchRequest with query and parameters

    Returns:
        SearchResponse with similar products
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        # Search
        results = search_engine.search_by_text(
            request.query,
            k=request.k,
            search_mode=request.search_mode
        )

        return SearchResponse(
            query_type="text",
            results=[SearchResult(**r) for r in results],
            num_results=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text search: {str(e)}")


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """
    Get details for a specific product

    Args:
        product_id: Product ID

    Returns:
        Product details
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        product = search_engine.get_product_by_id(product_id)

        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        return product

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving product: {str(e)}")


@app.get("/categories")
async def get_categories():
    """
    Get list of available product categories

    Returns:
        List of categories
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        categories = search_engine.get_categories()
        return {
            "categories": categories,
            "num_categories": len(categories)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving categories: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
