"""
Advanced Search Engine with Hybrid Queries, Reranking, and Caching
Extended version with production features
"""

import os
import sys
from typing import List, Dict, Optional, Tuple
import numpy as np
from PIL import Image
import hashlib
import json
import time

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from build_embeddings import CLIPEmbedder
from build_vector_db import VectorDatabase


class AdvancedSearchEngine:
    """
    Advanced search engine with:
    - Hybrid image+text queries
    - Cross-encoder reranking
    - Category filtering
    - Price range filtering
    - Redis caching (optional)
    - Query analytics
    """

    def __init__(
        self,
        vector_db_path: str,
        model_name: str = 'clip-ViT-B-32',
        use_cache: bool = True,
        use_reranking: bool = False
    ):
        """
        Initialize advanced search engine

        Args:
            vector_db_path: Path to saved vector database
            model_name: CLIP model name
            use_cache: Enable Redis caching
            use_reranking: Enable cross-encoder reranking
        """
        print(f"Initializing AdvancedSearchEngine...")

        # Load vector database
        self.vector_db = VectorDatabase.load(vector_db_path)

        # Initialize CLIP embedder
        self.embedder = CLIPEmbedder(model_name)

        # Initialize cache
        self.use_cache = use_cache
        self.cache = self._init_cache() if use_cache else None

        # Initialize reranker
        self.use_reranking = use_reranking
        self.reranker = self._init_reranker() if use_reranking else None

        # Analytics
        self.query_stats = {
            'total_queries': 0,
            'cache_hits': 0,
            'avg_latency': 0.0
        }

        print(f"✅ AdvancedSearchEngine ready")
        print(f"   - Model: {model_name}")
        print(f"   - Products: {len(self.vector_db.metadata)}")
        print(f"   - Cache: {'Enabled' if use_cache else 'Disabled'}")
        print(f"   - Reranking: {'Enabled' if use_reranking else 'Disabled'}")

    def _init_cache(self):
        """Initialize Redis cache (optional)"""
        try:
            import redis
            cache = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True
            )
            cache.ping()
            print("   - Redis cache connected")
            return cache
        except Exception as e:
            print(f"   - Redis cache unavailable: {e}")
            return None

    def _init_reranker(self):
        """Initialize cross-encoder for reranking"""
        try:
            from sentence_transformers import CrossEncoder
            reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("   - Cross-encoder reranker loaded")
            return reranker
        except Exception as e:
            print(f"   - Reranker unavailable: {e}")
            return None

    def search_hybrid(
        self,
        image: Optional[Image.Image] = None,
        text: Optional[str] = None,
        k: int = 5,
        alpha: float = 0.5,
        category: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None,
        rerank: bool = True
    ) -> List[Dict]:
        """
        Hybrid search combining image and text queries

        Args:
            image: PIL Image object (optional)
            text: Text query (optional)
            k: Number of results to return
            alpha: Weight for image vs text (0=text only, 1=image only)
            category: Filter by category
            price_range: (min_price, max_price) tuple
            rerank: Use cross-encoder reranking

        Returns:
            List of result dictionaries
        """
        start_time = time.time()

        # Check cache
        cache_key = self._get_cache_key(image, text, k, alpha, category, price_range)
        if self.cache and cache_key:
            cached = self._get_from_cache(cache_key)
            if cached:
                self.query_stats['cache_hits'] += 1
                return cached

        # Encode queries
        image_embedding = None
        text_embedding = None

        if image:
            image_embedding = self.embedder.encode_image_from_pil(image)

        if text:
            text_embedding = self.embedder.encode_text(text)

        # Combine embeddings
        if image_embedding is not None and text_embedding is not None:
            # Hybrid: weighted combination
            query_embedding = alpha * image_embedding + (1 - alpha) * text_embedding
            # Re-normalize
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        elif image_embedding is not None:
            query_embedding = image_embedding
        elif text_embedding is not None:
            query_embedding = text_embedding
        else:
            return []

        # Search with larger k for filtering/reranking
        search_k = k * 3 if (category or price_range or rerank) else k

        # Search in image index (generally better for hybrid)
        distances, indices = self.vector_db.search_image(
            query_embedding,
            k=search_k,
            use_image_index=True
        )

        # Get results
        results = self.vector_db.get_results(indices, distances)

        # Apply filters
        if category:
            results = [r for r in results if r.get('category') == category]

        if price_range:
            min_price, max_price = price_range
            results = [
                r for r in results
                if min_price <= r.get('price', 0) <= max_price
            ]

        # Rerank if enabled and text query provided
        if rerank and self.reranker and text:
            results = self._rerank_results(results, text, k)
        else:
            results = results[:k]

        # Cache results
        if self.cache and cache_key:
            self._save_to_cache(cache_key, results)

        # Update stats
        latency = time.time() - start_time
        self._update_stats(latency)

        return results

    def search_by_image(
        self,
        image: Image.Image,
        k: int = 5,
        search_mode: str = "image",
        category: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None
    ) -> List[Dict]:
        """
        Enhanced image search with filtering

        Args:
            image: PIL Image object
            k: Number of results to return
            search_mode: "image" or "text" (cross-modal)
            category: Filter by category
            price_range: (min_price, max_price) tuple

        Returns:
            List of result dictionaries
        """
        # Encode image
        query_embedding = self.embedder.encode_image_from_pil(image)

        if query_embedding is None:
            return []

        # Search with larger k for filtering
        search_k = k * 3 if (category or price_range) else k

        # Search
        use_image_index = (search_mode == "image")
        distances, indices = self.vector_db.search_image(
            query_embedding,
            k=search_k,
            use_image_index=use_image_index
        )

        # Get results
        results = self.vector_db.get_results(indices, distances)

        # Apply filters
        if category:
            results = [r for r in results if r.get('category') == category]

        if price_range:
            min_price, max_price = price_range
            results = [
                r for r in results
                if min_price <= r.get('price', 0) <= max_price
            ]

        return results[:k]

    def search_by_text(
        self,
        query: str,
        k: int = 5,
        search_mode: str = "text",
        category: Optional[str] = None,
        price_range: Optional[Tuple[float, float]] = None,
        rerank: bool = True
    ) -> List[Dict]:
        """
        Enhanced text search with filtering and reranking

        Args:
            query: Text query string
            k: Number of results to return
            search_mode: "text" or "image" (cross-modal)
            category: Filter by category
            price_range: (min_price, max_price) tuple
            rerank: Use cross-encoder reranking

        Returns:
            List of result dictionaries
        """
        # Encode text
        query_embedding = self.embedder.encode_text(query)

        if query_embedding is None:
            return []

        # Search with larger k for filtering/reranking
        search_k = k * 3 if (category or price_range or rerank) else k

        # Search
        use_text_index = (search_mode == "text")
        distances, indices = self.vector_db.search_text(
            query_embedding,
            k=search_k,
            use_text_index=use_text_index
        )

        # Get results
        results = self.vector_db.get_results(indices, distances)

        # Apply filters
        if category:
            results = [r for r in results if r.get('category') == category]

        if price_range:
            min_price, max_price = price_range
            results = [
                r for r in results
                if min_price <= r.get('price', 0) <= max_price
            ]

        # Rerank if enabled
        if rerank and self.reranker:
            results = self._rerank_results(results, query, k)
        else:
            results = results[:k]

        return results

    def _rerank_results(self, results: List[Dict], query: str, k: int) -> List[Dict]:
        """
        Rerank results using cross-encoder

        Args:
            results: Initial search results
            query: Query text
            k: Number of final results

        Returns:
            Reranked results
        """
        if not self.reranker or not results:
            return results[:k]

        # Prepare pairs for cross-encoder
        pairs = []
        for r in results:
            doc_text = f"{r.get('title', '')} {r.get('description', '')}"
            pairs.append([query, doc_text])

        # Get reranking scores
        scores = self.reranker.predict(pairs)

        # Add scores to results
        for i, score in enumerate(scores):
            results[i]['rerank_score'] = float(score)
            # Combine with original similarity
            results[i]['combined_score'] = (
                0.7 * results[i]['similarity_score'] +
                0.3 * (1 / (1 + np.exp(-score)))  # Sigmoid of rerank score
            )

        # Sort by combined score
        results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

        return results[:k]

    def _get_cache_key(self, image, text, k, alpha, category, price_range):
        """Generate cache key for query"""
        if not self.cache:
            return None

        key_parts = []

        if image:
            # Hash image
            import io
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='JPEG')
            img_hash = hashlib.md5(img_bytes.getvalue()).hexdigest()
            key_parts.append(f"img:{img_hash}")

        if text:
            key_parts.append(f"txt:{text}")

        key_parts.extend([
            f"k:{k}",
            f"alpha:{alpha}",
            f"cat:{category or 'none'}",
            f"price:{price_range or 'none'}"
        ])

        return "query:" + hashlib.md5(":".join(key_parts).encode()).hexdigest()

    def _get_from_cache(self, key: str) -> Optional[List[Dict]]:
        """Get results from cache"""
        try:
            cached = self.cache.get(key)
            if cached:
                return json.loads(cached)
        except:
            pass
        return None

    def _save_to_cache(self, key: str, results: List[Dict], ttl: int = 3600):
        """Save results to cache"""
        try:
            self.cache.setex(key, ttl, json.dumps(results))
        except:
            pass

    def _update_stats(self, latency: float):
        """Update query statistics"""
        self.query_stats['total_queries'] += 1
        n = self.query_stats['total_queries']
        self.query_stats['avg_latency'] = (
            (self.query_stats['avg_latency'] * (n - 1) + latency) / n
        )

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """Get product details by ID"""
        product = self.vector_db.metadata[
            self.vector_db.metadata['id'] == product_id
        ]

        if len(product) == 0:
            return None

        return product.iloc[0].to_dict()

    def get_categories(self) -> List[str]:
        """Get list of unique categories"""
        if 'category' not in self.vector_db.metadata.columns:
            return []

        return sorted(self.vector_db.metadata['category'].unique().tolist())

    def get_price_range(self) -> Tuple[float, float]:
        """Get min and max prices in catalog"""
        if 'price' not in self.vector_db.metadata.columns:
            return (0.0, 100.0)

        return (
            float(self.vector_db.metadata['price'].min()),
            float(self.vector_db.metadata['price'].max())
        )

    def get_stats(self) -> Dict:
        """Get query statistics"""
        stats = self.query_stats.copy()
        if stats['total_queries'] > 0:
            stats['cache_hit_rate'] = stats['cache_hits'] / stats['total_queries']
        else:
            stats['cache_hit_rate'] = 0.0
        return stats
