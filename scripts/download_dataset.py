"""
Dataset Download and Preparation Script
Downloads sample retail product dataset for the Multi-Modal Retail Assistant
"""

import os
import pandas as pd
import requests
from PIL import Image
import io
import argparse
from tqdm import tqdm


def download_sample_fashion_dataset(output_dir='data', num_samples=100):
    """
    Download sample fashion product images from public APIs

    Args:
        output_dir: Directory to save images and metadata
        num_samples: Number of samples to download
    """
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

    # Sample fashion products data
    products = []
    categories = ['tshirt', 'shoes', 'jeans', 'dress', 'jacket', 'bag', 'watch', 'sunglasses']

    print(f"Creating sample dataset with {num_samples} products...")

    for i in range(num_samples):
        category = categories[i % len(categories)]
        product_id = f"PROD_{i:05d}"

        # Create product metadata
        product = {
            'id': product_id,
            'title': f"{category.capitalize()} Style {i}",
            'description': f"High quality {category} for everyday wear. Comfortable and stylish.",
            'category': category,
            'brand': f"Brand{i % 10}",
            'price': round(20 + (i % 100), 2),
            'image_path': f"data/images/{product_id}.jpg"
        }
        products.append(product)

    # Save metadata
    df = pd.DataFrame(products)
    metadata_path = os.path.join(output_dir, 'metadata.csv')
    df.to_csv(metadata_path, index=False)
    print(f"✅ Metadata saved to {metadata_path}")

    return df


def download_unsplash_images(search_terms, output_dir='data/images', num_per_term=10):
    """
    Download sample images from Unsplash (requires API key)

    Args:
        search_terms: List of search terms
        output_dir: Directory to save images
        num_per_term: Number of images per search term
    """
    # Note: This requires UNSPLASH_ACCESS_KEY environment variable
    access_key = os.getenv('UNSPLASH_ACCESS_KEY')

    if not access_key:
        print("⚠️  UNSPLASH_ACCESS_KEY not found. Skipping image download.")
        print("   To download real images, sign up at https://unsplash.com/developers")
        print("   and set UNSPLASH_ACCESS_KEY environment variable")
        return

    os.makedirs(output_dir, exist_ok=True)
    base_url = "https://api.unsplash.com/search/photos"

    image_count = 0

    for term in tqdm(search_terms, desc="Downloading images"):
        params = {
            'query': term,
            'per_page': num_per_term,
            'client_id': access_key
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()

            for idx, photo in enumerate(data.get('results', [])):
                try:
                    img_url = photo['urls']['regular']
                    img_response = requests.get(img_url)
                    img_response.raise_for_status()

                    img = Image.open(io.BytesIO(img_response.content))
                    img = img.convert('RGB')

                    # Save image
                    filename = f"PROD_{image_count:05d}.jpg"
                    img.save(os.path.join(output_dir, filename))
                    image_count += 1

                except Exception as e:
                    print(f"Error downloading image: {e}")
                    continue

        except Exception as e:
            print(f"Error searching for '{term}': {e}")
            continue

    print(f"✅ Downloaded {image_count} images to {output_dir}")


def create_placeholder_images(metadata_df, output_dir='data/images'):
    """
    Create placeholder images for testing when real images are not available

    Args:
        metadata_df: DataFrame with product metadata
        output_dir: Directory to save images
    """
    from PIL import ImageDraw, ImageFont

    os.makedirs(output_dir, exist_ok=True)

    colors = [
        (255, 182, 193),  # Pink
        (173, 216, 230),  # Light Blue
        (144, 238, 144),  # Light Green
        (255, 218, 185),  # Peach
        (221, 160, 221),  # Plum
        (255, 255, 224),  # Light Yellow
        (255, 228, 196),  # Bisque
        (230, 230, 250),  # Lavender
    ]

    print("Creating placeholder images...")

    for idx, row in tqdm(metadata_df.iterrows(), total=len(metadata_df)):
        # Create image
        img = Image.new('RGB', (400, 400), color=colors[idx % len(colors)])
        draw = ImageDraw.Draw(img)

        # Add text
        text = f"{row['category'].upper()}\n{row['title']}\n${row['price']}"

        # Draw text in center
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (400 - text_width) // 2
        y = (400 - text_height) // 2

        draw.text((x, y), text, fill=(0, 0, 0))

        # Save
        filename = f"PROD_{idx:05d}.jpg"
        img.save(os.path.join(output_dir, filename))

    print(f"✅ Created {len(metadata_df)} placeholder images in {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download and prepare retail product dataset")
    parser.add_argument('--num-samples', type=int, default=100,
                       help='Number of product samples to generate')
    parser.add_argument('--output-dir', type=str, default='data',
                       help='Output directory for data')
    parser.add_argument('--use-unsplash', action='store_true',
                       help='Download real images from Unsplash (requires API key)')
    parser.add_argument('--placeholder', action='store_true', default=True,
                       help='Create placeholder images for testing')

    args = parser.parse_args()

    # Create metadata
    df = download_sample_fashion_dataset(args.output_dir, args.num_samples)

    # Download or create images
    if args.use_unsplash:
        categories = df['category'].unique().tolist()
        download_unsplash_images(categories, os.path.join(args.output_dir, 'images'))
    elif args.placeholder:
        create_placeholder_images(df, os.path.join(args.output_dir, 'images'))

    print("\n✅ Dataset preparation complete!")
    print(f"   - Metadata: {args.output_dir}/metadata.csv")
    print(f"   - Images: {args.output_dir}/images/")
    print(f"\nNext steps:")
    print(f"   1. Run: python scripts/build_embeddings.py")
    print(f"   2. Run: python scripts/build_vector_db.py")
    print(f"   3. Start backend: cd backend && uvicorn main:app --reload")
    print(f"   4. Start frontend: cd frontend && streamlit run app.py")
