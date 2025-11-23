"""
Vector Database Builder using FAISS
Creates searchable indexes for image and text embeddings
"""

import os
import numpy as np
import pandas as pd
import faiss
import pickle
import argparse
from pathlib import Path


class VectorDatabase:
    """FAISS-based vector database for similarity search"""

    def __init__(self, embedding_dim=512):
        """
        Initialize vector database

        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.image_index = None
        self.text_index = None
        self.metadata = None

    def build_index(self, embeddings, index_type='flat'):
        """
        Build FAISS index from embeddings

        Args:
            embeddings: numpy array of shape (n_samples, embedding_dim)
            index_type: Type of FAISS index ('flat', 'ivf', 'hnsw')

        Returns:
            FAISS index
        """
        n_samples = embeddings.shape[0]

        if index_type == 'flat':
            # L2 distance (Euclidean)
            index = faiss.IndexFlatL2(self.embedding_dim)
        elif index_type == 'ivf':
            # Inverted File Index for faster search (approximate)
            nlist = min(100, n_samples // 10)  # Number of clusters
            quantizer = faiss.IndexFlatL2(self.embedding_dim)
            index = faiss.IndexIVFFlat(quantizer, self.embedding_dim, nlist)
            index.train(embeddings)
        elif index_type == 'hnsw':
            # Hierarchical Navigable Small World for fast approximate search
            index = faiss.IndexHNSWFlat(self.embedding_dim, 32)
        else:
            raise ValueError(f"Unknown index type: {index_type}")

        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)

        # Add vectors to index
        index.add(embeddings)

        return index

    def build_from_embeddings(self, image_embeddings, text_embeddings, metadata, index_type='flat'):
        """
        Build indexes from pre-computed embeddings

        Args:
            image_embeddings: numpy array of image embeddings
            text_embeddings: numpy array of text embeddings
            metadata: pandas DataFrame with product metadata
            index_type: Type of FAISS index to use
        """
        print(f"Building FAISS indexes with type: {index_type}")

        # Build image index
        print(f"Building image index from {image_embeddings.shape[0]} embeddings...")
        self.image_index = self.build_index(image_embeddings, index_type)

        # Build text index
        print(f"Building text index from {text_embeddings.shape[0]} embeddings...")
        self.text_index = self.build_index(text_embeddings, index_type)

        # Store metadata
        self.metadata = metadata

        print(f"✅ Indexes built successfully")
        print(f"   - Image index: {self.image_index.ntotal} vectors")
        print(f"   - Text index: {self.text_index.ntotal} vectors")

    def search_image(self, query_embedding, k=5, use_image_index=True):
        """
        Search for similar items using image query

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            use_image_index: If True, search image index; else search text index

        Returns:
            distances: Array of distances to nearest neighbors
            indices: Array of indices of nearest neighbors
        """
        query = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query)

        index = self.image_index if use_image_index else self.text_index
        distances, indices = index.search(query, k)

        return distances[0], indices[0]

    def search_text(self, query_embedding, k=5, use_text_index=True):
        """
        Search for similar items using text query

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            use_text_index: If True, search text index; else search image index

        Returns:
            distances: Array of distances to nearest neighbors
            indices: Array of indices of nearest neighbors
        """
        query = query_embedding.reshape(1, -1).astype('float32')
        faiss.normalize_L2(query)

        index = self.text_index if use_text_index else self.image_index
        distances, indices = index.search(query, k)

        return distances[0], indices[0]

    def get_results(self, indices, distances):
        """
        Get metadata for search results

        Args:
            indices: Array of result indices
            distances: Array of distances/scores

        Returns:
            List of result dictionaries
        """
        results = []

        for idx, dist in zip(indices, distances):
            if idx < len(self.metadata):
                result = self.metadata.iloc[idx].to_dict()
                result['similarity_score'] = float(1 / (1 + dist))  # Convert distance to similarity
                result['distance'] = float(dist)
                results.append(result)

        return results

    def save(self, output_dir):
        """
        Save indexes and metadata to disk

        Args:
            output_dir: Directory to save files
        """
        os.makedirs(output_dir, exist_ok=True)

        # Save FAISS indexes
        faiss.write_index(self.image_index, os.path.join(output_dir, 'image_index.faiss'))
        faiss.write_index(self.text_index, os.path.join(output_dir, 'text_index.faiss'))

        # Save metadata
        self.metadata.to_csv(os.path.join(output_dir, 'metadata.csv'), index=False)

        # Save config
        config = {
            'embedding_dim': self.embedding_dim,
            'num_vectors': self.image_index.ntotal
        }

        with open(os.path.join(output_dir, 'db_config.pkl'), 'wb') as f:
            pickle.dump(config, f)

        print(f"✅ Vector database saved to {output_dir}")

    @classmethod
    def load(cls, input_dir):
        """
        Load indexes and metadata from disk

        Args:
            input_dir: Directory containing saved files

        Returns:
            VectorDatabase instance
        """
        # Load config
        with open(os.path.join(input_dir, 'db_config.pkl'), 'rb') as f:
            config = pickle.load(f)

        # Create instance
        db = cls(embedding_dim=config['embedding_dim'])

        # Load FAISS indexes
        db.image_index = faiss.read_index(os.path.join(input_dir, 'image_index.faiss'))
        db.text_index = faiss.read_index(os.path.join(input_dir, 'text_index.faiss'))

        # Load metadata
        db.metadata = pd.read_csv(os.path.join(input_dir, 'metadata.csv'))

        print(f"✅ Vector database loaded from {input_dir}")
        print(f"   - Image index: {db.image_index.ntotal} vectors")
        print(f"   - Text index: {db.text_index.ntotal} vectors")
        print(f"   - Metadata: {len(db.metadata)} products")

        return db


def build_vector_database(embeddings_dir, output_dir, index_type='flat'):
    """
    Build vector database from embeddings directory

    Args:
        embeddings_dir: Directory containing embeddings and metadata
        output_dir: Directory to save vector database
        index_type: Type of FAISS index to build
    """
    # Load embeddings
    print(f"Loading embeddings from {embeddings_dir}")
    image_embeddings = np.load(os.path.join(embeddings_dir, 'image_embeddings.npy'))
    text_embeddings = np.load(os.path.join(embeddings_dir, 'text_embeddings.npy'))
    metadata = pd.read_csv(os.path.join(embeddings_dir, 'metadata_with_embeddings.csv'))

    print(f"Loaded embeddings:")
    print(f"  - Images: {image_embeddings.shape}")
    print(f"  - Texts: {text_embeddings.shape}")
    print(f"  - Metadata: {len(metadata)} products")

    # Create database
    embedding_dim = image_embeddings.shape[1]
    db = VectorDatabase(embedding_dim=embedding_dim)

    # Build indexes
    db.build_from_embeddings(image_embeddings, text_embeddings, metadata, index_type)

    # Save database
    db.save(output_dir)

    return db


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build FAISS vector database")
    parser.add_argument('--embeddings-dir', type=str, default='data/embeddings',
                       help='Directory containing embeddings')
    parser.add_argument('--output-dir', type=str, default='data/vector_db',
                       help='Output directory for vector database')
    parser.add_argument('--index-type', type=str, default='flat',
                       choices=['flat', 'ivf', 'hnsw'],
                       help='Type of FAISS index to build')

    args = parser.parse_args()

    build_vector_database(args.embeddings_dir, args.output_dir, args.index_type)

    print("\n✅ Vector database build complete!")
    print(f"\nNext steps:")
    print(f"   1. Start backend: cd backend && uvicorn main:app --reload")
    print(f"   2. Start frontend: cd frontend && streamlit run app.py")
