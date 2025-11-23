"""
Tests for CLIP embedding generation
"""

import pytest
import numpy as np
from PIL import Image
import sys
import os

# Add scripts to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))

from build_embeddings import CLIPEmbedder


@pytest.fixture
def embedder():
    """Create CLIPEmbedder instance"""
    return CLIPEmbedder(model_name='clip-ViT-B-32')


def test_embedder_initialization(embedder):
    """Test that embedder initializes correctly"""
    assert embedder is not None
    assert embedder.model is not None
    assert embedder.embedding_dim > 0


def test_text_encoding(embedder):
    """Test text encoding"""
    text = "red running shoes"
    embedding = embedder.encode_text(text)

    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] == embedder.embedding_dim


def test_image_encoding_from_pil(embedder):
    """Test PIL image encoding"""
    # Create a dummy image
    img = Image.new('RGB', (224, 224), color='red')
    embedding = embedder.encode_image_from_pil(img)

    assert embedding is not None
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape[0] == embedder.embedding_dim


def test_embedding_consistency(embedder):
    """Test that same input produces same embedding"""
    text = "test product"

    embedding1 = embedder.encode_text(text)
    embedding2 = embedder.encode_text(text)

    assert np.allclose(embedding1, embedding2)


def test_embedding_difference(embedder):
    """Test that different inputs produce different embeddings"""
    text1 = "red shoes"
    text2 = "blue dress"

    embedding1 = embedder.encode_text(text1)
    embedding2 = embedder.encode_text(text2)

    # Embeddings should be different
    assert not np.allclose(embedding1, embedding2)


def test_batch_text_encoding(embedder):
    """Test batch text encoding"""
    texts = ["product 1", "product 2", "product 3"]
    embeddings = embedder.encode_text_batch(texts, batch_size=2)

    assert embeddings is not None
    assert isinstance(embeddings, np.ndarray)
    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] == embedder.embedding_dim


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
