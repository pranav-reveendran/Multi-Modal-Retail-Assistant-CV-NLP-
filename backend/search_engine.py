"""
Search Engine for Multi-Modal Retail Assistant
Handles image and text search using CLIP and FAISS
"""

import os
import sys
from typing import List, Dict, Optional
import numpy as np
from PIL import Image

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from build_embeddings import CLIPEmbedder
from build_vector_db import VectorDatabase


class SearchEngine:
    """Search engine combining CLIP embeddings and FAISS vector search"""

    def __init__(self, vector_db_path: str, model_name: str = 'clip-ViT-B-32'):
        """
        Initialize search engine

        Args:
            vector_db_path: Path to saved vector database
            model_name: CLIP model name
        """
        print(f"Initializing SearchEngine...")

        # Load vector database
        self.vector_db = VectorDatabase.load(vector_db_path)

        # Initialize CLIP embedder
        self.embedder = CLIPEmbedder(model_name)

        print(f"✅ SearchEngine ready")
        print(f"   - Model: {model_name}")
        print(f"   - Products: {len(self.vector_db.metadata)}")

    def search_by_image(
        self,
        image: Image.Image,
        k: int = 5,
        search_mode: str = "image"
    ) -> List[Dict]:
        """
        Search for similar products using an image

        Args:
            image: PIL Image object
            k: Number of results to return
            search_mode: "image" to search image index, "text" to search text index (cross-modal)

        Returns:
            List of result dictionaries
        """
        # Encode image
        query_embedding = self.embedder.encode_image_from_pil(image)

        if query_embedding is None:
            return []

        # Search
        use_image_index = (search_mode == "image")
        distances, indices = self.vector_db.search_image(
            query_embedding,
            k=k,
            use_image_index=use_image_index
        )

        # Get results
        results = self.vector_db.get_results(indices, distances)

        return results

    def search_by_text(
        self,
        query: str,
        k: int = 5,
        search_mode: str = "text"
    ) -> List[Dict]:
        """
        Search for similar products using a text query

        Args:
            query: Text query string
            k: Number of results to return
            search_mode: "text" to search text index, "image" to search image index (cross-modal)

        Returns:
            List of result dictionaries
        """
        # Encode text
        query_embedding = self.embedder.encode_text(query)

        if query_embedding is None:
            return []

        # Search
        use_text_index = (search_mode == "text")
        distances, indices = self.vector_db.search_text(
            query_embedding,
            k=k,
            use_text_index=use_text_index
        )

        # Get results
        results = self.vector_db.get_results(indices, distances)

        return results

    def get_product_by_id(self, product_id: str) -> Optional[Dict]:
        """
        Get product details by ID

        Args:
            product_id: Product ID

        Returns:
            Product dictionary or None
        """
        product = self.vector_db.metadata[
            self.vector_db.metadata['id'] == product_id
        ]

        if len(product) == 0:
            return None

        return product.iloc[0].to_dict()

    def get_categories(self) -> List[str]:
        """
        Get list of unique categories

        Returns:
            List of category names
        """
        if 'category' not in self.vector_db.metadata.columns:
            return []

        return sorted(self.vector_db.metadata['category'].unique().tolist())

    def filter_by_category(
        self,
        results: List[Dict],
        category: str
    ) -> List[Dict]:
        """
        Filter results by category

        Args:
            results: List of search results
            category: Category to filter by

        Returns:
            Filtered results
        """
        return [r for r in results if r.get('category') == category]
