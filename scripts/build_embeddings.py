"""
Embedding Pipeline for Multi-Modal Retail Assistant
Generates CLIP embeddings for images and text descriptions
"""

import os
import numpy as np
import pandas as pd
from PIL import Image
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import pickle
import argparse


class CLIPEmbedder:
    """CLIP-based encoder for images and text"""

    def __init__(self, model_name='clip-ViT-B-32'):
        """
        Initialize CLIP model

        Args:
            model_name: Name of the CLIP model to use
        """
        print(f"Loading CLIP model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        print(f"Model loaded. Embedding dimension: {self.embedding_dim}")

    def encode_image(self, image_path):
        """
        Encode a single image to embedding vector

        Args:
            image_path: Path to image file

        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            img = Image.open(image_path).convert("RGB")
            embedding = self.model.encode(img, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return None

    def encode_image_from_pil(self, image):
        """
        Encode a PIL Image directly to embedding vector

        Args:
            image: PIL Image object

        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            embedding = self.model.encode(image, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Error encoding PIL image: {e}")
            return None

    def encode_text(self, text):
        """
        Encode text to embedding vector

        Args:
            text: Text string to encode

        Returns:
            numpy array of shape (embedding_dim,)
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            print(f"Error encoding text: {e}")
            return None

    def encode_image_batch(self, image_paths, batch_size=32):
        """
        Encode multiple images in batches

        Args:
            image_paths: List of image paths
            batch_size: Number of images to process at once

        Returns:
            numpy array of shape (n_images, embedding_dim)
        """
        embeddings = []

        for i in tqdm(range(0, len(image_paths), batch_size), desc="Encoding images"):
            batch_paths = image_paths[i:i+batch_size]
            batch_images = []

            for path in batch_paths:
                try:
                    img = Image.open(path).convert("RGB")
                    batch_images.append(img)
                except Exception as e:
                    print(f"Error loading {path}: {e}")
                    batch_images.append(None)

            # Filter out None values
            valid_images = [img for img in batch_images if img is not None]

            if valid_images:
                batch_embeddings = self.model.encode(valid_images, convert_to_numpy=True, batch_size=len(valid_images))
                embeddings.extend(batch_embeddings)

        return np.array(embeddings)

    def encode_text_batch(self, texts, batch_size=32):
        """
        Encode multiple texts in batches

        Args:
            texts: List of text strings
            batch_size: Number of texts to process at once

        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        embeddings = []

        for i in tqdm(range(0, len(texts), batch_size), desc="Encoding texts"):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch_texts, convert_to_numpy=True, batch_size=len(batch_texts))
            embeddings.extend(batch_embeddings)

        return np.array(embeddings)


def build_embeddings_from_metadata(metadata_path, output_dir, model_name='clip-ViT-B-32'):
    """
    Build embeddings from metadata CSV file

    Args:
        metadata_path: Path to metadata CSV with columns: id, image_path, title, description, category
        output_dir: Directory to save embeddings
        model_name: CLIP model name
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Load metadata
    print(f"Loading metadata from {metadata_path}")
    df = pd.read_csv(metadata_path)
    print(f"Loaded {len(df)} products")

    # Initialize embedder
    embedder = CLIPEmbedder(model_name)

    # Encode images
    print("\n=== Encoding Images ===")
    image_paths = df['image_path'].tolist()
    image_embeddings = embedder.encode_image_batch(image_paths)

    # Encode text (combine title and description if available)
    print("\n=== Encoding Text ===")
    if 'description' in df.columns:
        texts = (df['title'] + " " + df['description'].fillna("")).tolist()
    else:
        texts = df['title'].tolist()

    text_embeddings = embedder.encode_text_batch(texts)

    # Save embeddings
    print("\n=== Saving Embeddings ===")
    np.save(os.path.join(output_dir, 'image_embeddings.npy'), image_embeddings)
    np.save(os.path.join(output_dir, 'text_embeddings.npy'), text_embeddings)

    # Add embeddings to dataframe and save
    df['image_embedding_idx'] = range(len(df))
    df['text_embedding_idx'] = range(len(df))
    df.to_csv(os.path.join(output_dir, 'metadata_with_embeddings.csv'), index=False)

    # Save embedder config
    config = {
        'model_name': model_name,
        'embedding_dim': embedder.embedding_dim,
        'num_products': len(df)
    }

    with open(os.path.join(output_dir, 'embedder_config.pkl'), 'wb') as f:
        pickle.dump(config, f)

    print(f"\n✅ Embeddings saved to {output_dir}")
    print(f"   - Image embeddings: {image_embeddings.shape}")
    print(f"   - Text embeddings: {text_embeddings.shape}")
    print(f"   - Metadata: {len(df)} products")

    return image_embeddings, text_embeddings, df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build CLIP embeddings for retail products")
    parser.add_argument('--metadata', type=str, default='data/metadata.csv',
                       help='Path to metadata CSV file')
    parser.add_argument('--output', type=str, default='data/embeddings',
                       help='Output directory for embeddings')
    parser.add_argument('--model', type=str, default='clip-ViT-B-32',
                       help='CLIP model name')

    args = parser.parse_args()

    build_embeddings_from_metadata(args.metadata, args.output, args.model)
