"""
Advanced FastAPI Backend for Multi-Modal Retail Assistant
Enhanced version with hybrid queries, filtering, caching, and analytics
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Tuple
import os
import sys
from PIL import Image
import io
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.search_engine_advanced import AdvancedSearchEngine


# Initialize FastAPI app
app = FastAPI(
    title="Multi-Modal Retail Assistant API (Advanced)",
    description="Enhanced product search with hybrid queries, filtering, caching, and reranking",
    version="2.0.0"
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
class HybridSearchRequest(BaseModel):
    text: Optional[str] = None
    k: int = 5
    alpha: float = 0.5  # Weight for image vs text
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rerank: bool = True


class TextSearchRequest(BaseModel):
    query: str
    k: int = 5
    search_mode: str = "text"  # "text" or "image"
    category: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    rerank: bool = True


class FeedbackRequest(BaseModel):
    query_id: str
    product_id: str
    rating: int  # 1-5
    clicked: bool = False


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
    rerank_score: Optional[float] = None
    combined_score: Optional[float] = None


class SearchResponse(BaseModel):
    query_type: str
    results: List[SearchResult]
    num_results: int
    latency_ms: Optional[float] = None


class StatsResponse(BaseModel):
    total_queries: int
    cache_hits: int
    cache_hit_rate: float
    avg_latency: float
    num_products: int
    num_categories: int


@app.on_event("startup")
async def startup_event():
    """Initialize search engine on startup"""
    global search_engine

    # Get paths from environment variables or use defaults
    vector_db_path = os.getenv("VECTOR_DB_PATH", "data/vector_db")
    model_name = os.getenv("CLIP_MODEL_NAME", "clip-ViT-B-32")
    use_cache = os.getenv("USE_CACHE", "true").lower() == "true"
    use_reranking = os.getenv("USE_RERANKING", "false").lower() == "true"

    print(f"Initializing advanced search engine...")
    print(f"  - Vector DB path: {vector_db_path}")
    print(f"  - CLIP model: {model_name}")
    print(f"  - Cache: {use_cache}")
    print(f"  - Reranking: {use_reranking}")

    try:
        search_engine = AdvancedSearchEngine(
            vector_db_path=vector_db_path,
            model_name=model_name,
            use_cache=use_cache,
            use_reranking=use_reranking
        )
        print("✅ Advanced search engine initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing search engine: {e}")
        print("Make sure to run the setup scripts first:")
        print("  1. python scripts/download_real_dataset.py --dataset fashion")
        print("  2. python scripts/build_embeddings.py")
        print("  3. python scripts/build_vector_db.py")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Multi-Modal Retail Assistant API (Advanced)",
        "version": "2.0.0",
        "features": [
            "Hybrid image+text search",
            "Category filtering",
            "Price range filtering",
            "Cross-encoder reranking",
            "Redis caching",
            "Query analytics"
        ],
        "endpoints": {
            "search_image": "/search/image",
            "search_text": "/search/text",
            "search_hybrid": "/search/hybrid",
            "categories": "/categories",
            "price_range": "/price-range",
            "stats": "/stats",
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

    stats = search_engine.get_stats()

    return {
        "status": "healthy",
        "search_engine": "ready",
        "num_products": len(search_engine.vector_db.metadata),
        "cache_enabled": search_engine.use_cache,
        "reranking_enabled": search_engine.use_reranking,
        "stats": stats
    }


@app.post("/search/hybrid", response_model=SearchResponse)
async def search_hybrid(
    request: HybridSearchRequest,
    file: Optional[UploadFile] = File(None)
):
    """
    Hybrid search combining image and text queries

    Args:
        request: Search parameters
        file: Optional image file

    Returns:
        SearchResponse with similar products
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        import time
        start_time = time.time()

        # Process image if provided
        image = None
        if file:
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Build price range
        price_range = None
        if request.min_price is not None and request.max_price is not None:
            price_range = (request.min_price, request.max_price)

        # Search
        results = search_engine.search_hybrid(
            image=image,
            text=request.text,
            k=request.k,
            alpha=request.alpha,
            category=request.category,
            price_range=price_range,
            rerank=request.rerank
        )

        latency = (time.time() - start_time) * 1000  # Convert to ms

        return SearchResponse(
            query_type="hybrid",
            results=[SearchResult(**r) for r in results],
            num_results=len(results),
            latency_ms=latency
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing hybrid search: {str(e)}")


@app.post("/search/image", response_model=SearchResponse)
async def search_by_image(
    file: UploadFile = File(...),
    k: int = Query(5, ge=1, le=50),
    search_mode: str = Query("image", regex="^(image|text)$"),
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
):
    """
    Enhanced image search with filtering

    Args:
        file: Uploaded image file
        k: Number of results to return
        search_mode: "image" or "text" (cross-modal)
        category: Filter by category
        min_price: Minimum price
        max_price: Maximum price

    Returns:
        SearchResponse with similar products
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        import time
        start_time = time.time()

        # Read and process image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")

        # Build price range
        price_range = None
        if min_price is not None and max_price is not None:
            price_range = (min_price, max_price)

        # Search
        results = search_engine.search_by_image(
            image,
            k=k,
            search_mode=search_mode,
            category=category,
            price_range=price_range
        )

        latency = (time.time() - start_time) * 1000

        return SearchResponse(
            query_type="image",
            results=[SearchResult(**r) for r in results],
            num_results=len(results),
            latency_ms=latency
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image search: {str(e)}")


@app.post("/search/text", response_model=SearchResponse)
async def search_by_text(request: TextSearchRequest):
    """
    Enhanced text search with filtering and reranking

    Args:
        request: TextSearchRequest with query and parameters

    Returns:
        SearchResponse with similar products
    """
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        import time
        start_time = time.time()

        # Build price range
        price_range = None
        if request.min_price is not None and request.max_price is not None:
            price_range = (request.min_price, request.max_price)

        # Search
        results = search_engine.search_by_text(
            request.query,
            k=request.k,
            search_mode=request.search_mode,
            category=request.category,
            price_range=price_range,
            rerank=request.rerank
        )

        latency = (time.time() - start_time) * 1000

        return SearchResponse(
            query_type="text",
            results=[SearchResult(**r) for r in results],
            num_results=len(results),
            latency_ms=latency
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text search: {str(e)}")


@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get details for a specific product"""
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
    """Get list of available product categories"""
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


@app.get("/price-range")
async def get_price_range():
    """Get min and max prices in catalog"""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        min_price, max_price = search_engine.get_price_range()
        return {
            "min_price": min_price,
            "max_price": max_price
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving price range: {str(e)}")


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get query statistics and analytics"""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        stats = search_engine.get_stats()
        return StatsResponse(
            total_queries=stats['total_queries'],
            cache_hits=stats['cache_hits'],
            cache_hit_rate=stats['cache_hit_rate'],
            avg_latency=stats['avg_latency'],
            num_products=len(search_engine.vector_db.metadata),
            num_categories=len(search_engine.get_categories())
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """
    Submit user feedback for search results
    This can be used to improve search quality
    """
    # In production, save to database for analysis
    print(f"Feedback received: {feedback.dict()}")

    return {
        "status": "success",
        "message": "Feedback recorded"
    }


@app.get("/images/{product_id}")
async def get_product_image(product_id: str):
    """Serve product images"""
    if search_engine is None:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        product = search_engine.get_product_by_id(product_id)

        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")

        image_path = product.get('image_path')

        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image not found")

        return FileResponse(image_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
