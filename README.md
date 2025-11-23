# 🛍️ Multi-Modal Retail Assistant

A powerful product search application that combines Computer Vision and Natural Language Processing using CLIP embeddings. Upload an image or describe what you're looking for, and get visually and semantically similar products from your catalog.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## 🎯 Features

- **Multi-Modal Search**: Search by image OR text using the same embedding space
- **Cross-Modal Retrieval**: Find products with images using text queries and vice versa
- **CLIP Embeddings**: State-of-the-art vision-language model for semantic understanding
- **Fast Vector Search**: FAISS-powered similarity search with sub-second response times
- **Modern UI**: Clean, responsive Streamlit interface
- **RESTful API**: FastAPI backend for easy integration
- **Docker Support**: Full containerization for easy deployment

## 🏗️ Architecture

```
User → Streamlit Frontend (Port 8501)
          ↓
     FastAPI Backend (Port 8000)
          ↓
     CLIP Encoder (sentence-transformers)
          ↓
     FAISS Vector Database
          ↓
     Product Catalog (Images + Metadata)
```

## 📋 Prerequisites

- Python 3.10 or higher
- 4GB+ RAM (8GB recommended)
- CUDA-capable GPU (optional, for faster encoding)
- Docker & Docker Compose (optional, for containerized deployment)

## 🚀 Quick Start

### Option 1: Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Multi-Modal-Retail-Assistant-CV-NLP-.git
cd Multi-Modal-Retail-Assistant-CV-NLP-
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Prepare dataset**
```bash
# Generate sample dataset with placeholder images
python scripts/download_dataset.py --num-samples 100 --placeholder

# OR download real images from Unsplash (requires API key)
export UNSPLASH_ACCESS_KEY=your_api_key
python scripts/download_dataset.py --num-samples 100 --use-unsplash
```

5. **Build embeddings**
```bash
python scripts/build_embeddings.py --metadata data/metadata.csv --output data/embeddings
```

6. **Build vector database**
```bash
python scripts/build_vector_db.py --embeddings-dir data/embeddings --output-dir data/vector_db
```

7. **Start backend**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

8. **Start frontend** (in a new terminal)
```bash
streamlit run frontend/app.py
```

9. **Open your browser**
   - Frontend: http://localhost:8501
   - API docs: http://localhost:8000/docs

### Option 2: Docker Deployment

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

2. **Access the application**
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📁 Project Structure

```
Multi-Modal-Retail-Assistant-CV-NLP-/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── search_engine.py     # Search logic with CLIP + FAISS
│   └── __init__.py
├── frontend/
│   └── app.py               # Streamlit UI
├── scripts/
│   ├── download_dataset.py  # Dataset preparation
│   ├── build_embeddings.py  # CLIP embedding generation
│   └── build_vector_db.py   # FAISS index building
├── data/
│   ├── images/              # Product images
│   ├── embeddings/          # Generated embeddings (.npy)
│   ├── vector_db/           # FAISS indexes
│   └── metadata.csv         # Product metadata
├── requirements.txt
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# API Configuration
API_URL=http://localhost:8000

# Vector Database
VECTOR_DB_PATH=data/vector_db

# CLIP Model
CLIP_MODEL_NAME=clip-ViT-B-32

# Optional: Unsplash API for real images
UNSPLASH_ACCESS_KEY=your_key_here
```

### CLIP Models

You can use different CLIP models by changing the `CLIP_MODEL_NAME`:

- `clip-ViT-B-32` (default) - Good balance of speed and accuracy
- `clip-ViT-B-16` - Higher accuracy, slower
- `clip-ViT-L-14` - Best accuracy, requires more memory

### FAISS Index Types

Choose index type in `build_vector_db.py`:

- `flat` - Exact search, best accuracy (default for <10K products)
- `ivf` - Approximate search, faster for large catalogs
- `hnsw` - Hierarchical graph, best for very large catalogs

## 📊 Dataset Format

Your `metadata.csv` should have these columns:

```csv
id,title,description,category,brand,price,image_path
PROD_00001,Red T-Shirt,Comfortable cotton t-shirt,tshirt,BrandA,29.99,data/images/PROD_00001.jpg
PROD_00002,Blue Jeans,Classic denim jeans,jeans,BrandB,59.99,data/images/PROD_00002.jpg
```

**Required columns:**
- `id`: Unique product identifier
- `title`: Product name
- `category`: Product category
- `image_path`: Relative path to product image

**Optional columns:**
- `description`: Product description
- `brand`: Brand name
- `price`: Product price

## 🎨 Using Your Own Dataset

1. **Organize your images**
```bash
mkdir -p data/images
# Copy your product images to data/images/
```

2. **Create metadata.csv**
```python
import pandas as pd

data = {
    'id': ['PROD_001', 'PROD_002'],
    'title': ['Product 1', 'Product 2'],
    'description': ['Description 1', 'Description 2'],
    'category': ['category1', 'category2'],
    'brand': ['Brand A', 'Brand B'],
    'price': [29.99, 39.99],
    'image_path': ['data/images/001.jpg', 'data/images/002.jpg']
}

df = pd.DataFrame(data)
df.to_csv('data/metadata.csv', index=False)
```

3. **Generate embeddings and build index**
```bash
python scripts/build_embeddings.py
python scripts/build_vector_db.py
```

## 🔍 API Endpoints

### Search by Image
```bash
curl -X POST "http://localhost:8000/search/image?k=5" \
  -F "file=@product.jpg"
```

### Search by Text
```bash
curl -X POST "http://localhost:8000/search/text" \
  -H "Content-Type: application/json" \
  -d '{"query": "red running shoes", "k": 5}'
```

### Get Product Details
```bash
curl "http://localhost:8000/products/PROD_00001"
```

### List Categories
```bash
curl "http://localhost:8000/categories"
```

## 🎯 Use Cases

1. **E-commerce Visual Search**: Upload a product photo to find similar items
2. **Inventory Management**: Find duplicate or similar products in catalog
3. **Fashion Recommendations**: "Find dresses like this but in blue"
4. **Furniture Shopping**: Take a photo of a piece you like, find matches
5. **Grocery Shopping**: Search for snacks by image or description

## ⚡ Performance

### Benchmark Results (on sample dataset)

| Metric | Value |
|--------|-------|
| Embedding Generation | ~50 images/sec (CPU) |
| Search Latency | <100ms |
| Index Build Time | <10s for 10K products |
| Memory Usage | ~2GB for 10K products |

### Optimization Tips

1. **Use GPU for encoding** (10x faster):
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

2. **Batch processing for large datasets**:
```bash
python scripts/build_embeddings.py --batch-size 64
```

3. **Use IVF index for >10K products**:
```bash
python scripts/build_vector_db.py --index-type ivf
```

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if vector database exists
ls data/vector_db/

# Rebuild if missing
python scripts/build_vector_db.py
```

### Out of memory
```bash
# Reduce batch size
python scripts/build_embeddings.py --batch-size 16

# Use smaller CLIP model
export CLIP_MODEL_NAME=clip-ViT-B-32
```

### Slow search performance
```bash
# Use approximate index
python scripts/build_vector_db.py --index-type hnsw
```

## 🔮 Future Enhancements

- [ ] Add category filtering in search
- [ ] Implement hybrid image+text queries
- [ ] Add user feedback loop for reranking
- [ ] Support multiple languages
- [ ] Integrate with e-commerce platforms
- [ ] Add batch upload for multiple images
- [ ] Implement caching with Redis
- [ ] Add analytics dashboard
- [ ] Support video product search
- [ ] Mobile app integration

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [OpenAI CLIP](https://github.com/openai/CLIP) - Vision-language model
- [Sentence Transformers](https://www.sbert.net/) - CLIP implementation
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [Streamlit](https://streamlit.io/) - Interactive UI framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ using CLIP, FAISS, FastAPI, and Streamlit**
