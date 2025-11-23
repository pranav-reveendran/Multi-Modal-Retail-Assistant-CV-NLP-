"""
Real Dataset Downloader for Multi-Modal Retail Assistant
Downloads and prepares real product datasets from Kaggle and other sources
"""

import os
import sys
import pandas as pd
import requests
from pathlib import Path
import zipfile
import shutil
from tqdm import tqdm
import argparse
import json


class RealDatasetDownloader:
    """Download and prepare real product datasets"""

    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)

    def download_fashion_product_images(self):
        """
        Download Fashion Product Images Dataset from Kaggle
        Dataset: https://www.kaggle.com/datasets/paramaggarwal/fashion-product-images-dataset
        ~44K fashion products with images and metadata
        """
        print("📦 Downloading Fashion Product Images Dataset from Kaggle")
        print("=" * 60)

        # Check if kaggle is configured
        kaggle_json = Path.home() / '.kaggle' / 'kaggle.json'
        if not kaggle_json.exists():
            print("⚠️  Kaggle API credentials not found!")
            print("\nTo download from Kaggle:")
            print("1. Go to https://www.kaggle.com/settings/account")
            print("2. Click 'Create New API Token'")
            print("3. Move kaggle.json to ~/.kaggle/")
            print("4. Run: chmod 600 ~/.kaggle/kaggle.json")
            return False

        try:
            import kaggle

            # Download dataset
            dataset_name = "paramaggarwal/fashion-product-images-dataset"
            download_path = os.path.join(self.output_dir, 'raw')
            os.makedirs(download_path, exist_ok=True)

            print(f"Downloading {dataset_name}...")
            kaggle.api.dataset_download_files(
                dataset_name,
                path=download_path,
                unzip=True
            )

            # Process the dataset
            self._process_fashion_dataset(download_path)
            return True

        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            return False

    def _process_fashion_dataset(self, raw_path):
        """Process fashion product dataset"""
        print("\n📊 Processing Fashion Product Dataset...")

        # Load metadata
        styles_path = os.path.join(raw_path, 'styles.csv')
        if not os.path.exists(styles_path):
            print(f"❌ styles.csv not found in {raw_path}")
            return

        df = pd.read_csv(styles_path, on_bad_lines='skip')
        print(f"Loaded {len(df)} products")

        # Clean and prepare data
        df = df.dropna(subset=['id'])

        # Create standardized metadata
        metadata = []
        images_src = os.path.join(raw_path, 'images')
        images_dst = os.path.join(self.output_dir, 'images')

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Processing products"):
            product_id = f"PROD_{row['id']:05d}"

            # Source image path
            img_src = os.path.join(images_src, f"{row['id']}.jpg")

            if not os.path.exists(img_src):
                continue

            # Destination image path
            img_dst = os.path.join(images_dst, f"{product_id}.jpg")

            # Copy image
            try:
                shutil.copy2(img_src, img_dst)
            except Exception as e:
                print(f"Error copying {img_src}: {e}")
                continue

            # Create metadata entry
            entry = {
                'id': product_id,
                'title': row.get('productDisplayName', f'Product {row["id"]}'),
                'description': self._create_description(row),
                'category': row.get('articleType', 'Unknown'),
                'subcategory': row.get('subCategory', ''),
                'brand': row.get('brandName', ''),
                'price': self._generate_price(row),
                'color': row.get('baseColour', ''),
                'season': row.get('season', ''),
                'year': row.get('year', ''),
                'usage': row.get('usage', ''),
                'gender': row.get('gender', ''),
                'image_path': f"data/images/{product_id}.jpg"
            }

            metadata.append(entry)

        # Save metadata
        metadata_df = pd.DataFrame(metadata)
        metadata_path = os.path.join(self.output_dir, 'metadata.csv')
        metadata_df.to_csv(metadata_path, index=False)

        print(f"\n✅ Processed {len(metadata)} products")
        print(f"   - Metadata: {metadata_path}")
        print(f"   - Images: {images_dst}")

    def _create_description(self, row):
        """Create product description from available fields"""
        parts = []

        if pd.notna(row.get('productDisplayName')):
            parts.append(str(row['productDisplayName']))

        if pd.notna(row.get('baseColour')):
            parts.append(f"{row['baseColour']} color")

        if pd.notna(row.get('season')):
            parts.append(f"for {row['season']}")

        if pd.notna(row.get('usage')):
            parts.append(f"{row['usage']} use")

        return '. '.join(parts) if parts else 'Fashion product'

    def _generate_price(self, row):
        """Generate realistic price based on product type"""
        base_prices = {
            'Shirts': 29.99,
            'Tshirts': 19.99,
            'Jeans': 49.99,
            'Shoes': 59.99,
            'Watches': 99.99,
            'Bags': 39.99,
            'Sunglasses': 79.99,
            'Dress': 44.99,
        }

        article_type = row.get('articleType', 'Unknown')
        base_price = base_prices.get(article_type, 29.99)

        # Add variation based on brand/year
        variation = hash(str(row.get('brandName', ''))) % 20
        return round(base_price + variation, 2)

    def download_amazon_products(self):
        """
        Download Amazon Products Dataset
        Alternative dataset with product information
        """
        print("📦 Downloading Amazon Products Dataset")
        print("=" * 60)

        try:
            import kaggle

            dataset_name = "promptcloud/amazon-product-dataset-2020"
            download_path = os.path.join(self.output_dir, 'raw')
            os.makedirs(download_path, exist_ok=True)

            print(f"Downloading {dataset_name}...")
            kaggle.api.dataset_download_files(
                dataset_name,
                path=download_path,
                unzip=True
            )

            self._process_amazon_dataset(download_path)
            return True

        except Exception as e:
            print(f"❌ Error downloading dataset: {e}")
            return False

    def _process_amazon_dataset(self, raw_path):
        """Process Amazon product dataset"""
        print("\n📊 Processing Amazon Product Dataset...")

        csv_files = list(Path(raw_path).glob('*.csv'))
        if not csv_files:
            print("❌ No CSV files found")
            return

        df = pd.read_csv(csv_files[0])
        print(f"Loaded {len(df)} products")

        # Sample 1000 products with images
        df = df[df['image'].notna()].head(1000)

        metadata = []
        images_dst = os.path.join(self.output_dir, 'images')

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Downloading images"):
            product_id = f"PROD_{idx:05d}"

            # Download image
            try:
                img_url = row['image']
                img_path = os.path.join(images_dst, f"{product_id}.jpg")

                response = requests.get(img_url, timeout=10, stream=True)
                response.raise_for_status()

                with open(img_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                # Create metadata entry
                entry = {
                    'id': product_id,
                    'title': row.get('name', f'Product {idx}'),
                    'description': row.get('description', ''),
                    'category': row.get('category', 'General'),
                    'brand': row.get('brand', ''),
                    'price': self._parse_price(row.get('selling_price', '0')),
                    'image_path': f"data/images/{product_id}.jpg"
                }

                metadata.append(entry)

            except Exception as e:
                print(f"Error downloading image {idx}: {e}")
                continue

        # Save metadata
        metadata_df = pd.DataFrame(metadata)
        metadata_path = os.path.join(self.output_dir, 'metadata.csv')
        metadata_df.to_csv(metadata_path, index=False)

        print(f"\n✅ Processed {len(metadata)} products")

    def _parse_price(self, price_str):
        """Parse price from string"""
        try:
            import re
            numbers = re.findall(r'\d+\.?\d*', str(price_str))
            if numbers:
                return float(numbers[0])
        except:
            pass
        return 29.99

    def download_groceries_dataset(self):
        """
        Download grocery products dataset
        Grozi-120 or similar datasets
        """
        print("📦 Setting up Grocery Products Dataset")
        print("=" * 60)
        print("ℹ️  For grocery datasets, consider:")
        print("   - Grozi-120: http://grozi.calit2.net/")
        print("   - Freiburg Groceries: https://github.com/marcusklasson/GroceryStoreDataset")
        print("\nManual download may be required for some datasets.")


def main():
    parser = argparse.ArgumentParser(description="Download real product datasets")
    parser.add_argument(
        '--dataset',
        type=str,
        choices=['fashion', 'amazon', 'groceries', 'all'],
        default='fashion',
        help='Dataset to download'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data',
        help='Output directory'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of products to process'
    )

    args = parser.parse_args()

    downloader = RealDatasetDownloader(args.output_dir)

    if args.dataset == 'fashion' or args.dataset == 'all':
        downloader.download_fashion_product_images()

    if args.dataset == 'amazon' or args.dataset == 'all':
        downloader.download_amazon_products()

    if args.dataset == 'groceries':
        downloader.download_groceries_dataset()

    print("\n" + "=" * 60)
    print("✅ Dataset download complete!")
    print("\nNext steps:")
    print("   1. python scripts/build_embeddings.py")
    print("   2. python scripts/build_vector_db.py")
    print("   3. Start the application")


if __name__ == "__main__":
    main()
