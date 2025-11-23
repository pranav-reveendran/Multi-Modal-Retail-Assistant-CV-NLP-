# 🚀 Quick Start Guide

Get the Multi-Modal Retail Assistant running in 15 minutes!

## Prerequisites

- Python 3.10+
- 8GB RAM minimum
- 10GB free disk space
- Internet connection

## Option 1: Automated Setup (Recommended)

```bash
# 1. Clone and enter directory
git clone <repository-url>
cd Multi-Modal-Retail-Assistant-CV-NLP-

# 2. Run setup script
./setup.sh

# The script will:
# - Create virtual environment
# - Install dependencies
# - Generate sample dataset
# - Build embeddings
# - Build vector database
```

## Option 2: With Real Data (Fashion Dataset)

```bash
# 1. Setup Kaggle API
# Get your API key from https://www.kaggle.com/settings/account
mkdir -p ~/.kaggle
# Move downloaded kaggle.json to ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download Fashion Product Images dataset (44K products)
python scripts/download_real_dataset.py --dataset fashion

# This downloads ~3GB of data and may take 10-30 minutes

# 4. Build embeddings (20-30 minutes)
python scripts/build_embeddings.py

# 5. Build vector database (<1 minute)
python scripts/build_vector_db.py
```

## Starting the Application

### Basic Version

```bash
# Terminal 1: Start backend
uvicorn backend.main:app --reload

# Terminal 2: Start frontend
streamlit run frontend/app.py

# Open browser: http://localhost:8501
```

### Advanced Version (Recommended)

```bash
# Terminal 1: Start Redis (optional, for caching)
docker run -d -p 6379:6379 redis:7-alpine

# Terminal 2: Start advanced backend
export USE_CACHE=true
export REDIS_HOST=localhost
uvicorn backend.main_advanced:app --reload

# Terminal 3: Start advanced frontend
streamlit run frontend/app_advanced.py

# Open browser: http://localhost:8501
```

### Docker Version (Easiest)

```bash
# Basic
docker-compose up --build

# Advanced (with Redis)
docker-compose -f docker-compose-advanced.yml up --build

# Open browser: http://localhost:8501
```

## Using the Application

### 1. Image Search

1. Click "Image" search mode
2. Upload a product image
3. Adjust number of results (1-20)
4. Click "Search"
5. View similar products!

### 2. Text Search

1. Click "Text" search mode
2. Enter description: "red summer dress"
3. Enable reranking for better results
4. Click "Search"

### 3. Hybrid Search (Advanced)

1. Click "Hybrid" search mode
2. Upload image (optional)
3. Enter text description (optional)
4. Adjust image/text weight slider
5. Set filters:
   - Category (e.g., "Dresses")
   - Price range
6. Click "Search"

### 4. Filters (Advanced)

- **Category**: Select specific product type
- **Price Range**: Set min/max price
- **Results**: Choose 1-20 products
- **Reranking**: Toggle AI reranking (slower but more accurate)

## Troubleshooting

### "Backend API not available"

```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start backend
uvicorn backend.main_advanced:app --reload
```

### "Search engine not initialized"

```bash
# Make sure you've built the vector database
ls data/vector_db/

# If empty, rebuild:
python scripts/build_vector_db.py
```

### "Out of memory"

```bash
# Use smaller CLIP model
export CLIP_MODEL_NAME=clip-ViT-B-32

# Or reduce batch size
python scripts/build_embeddings.py --batch-size 16
```

### "Slow search"

```bash
# Enable caching
docker run -d -p 6379:6379 redis:7-alpine
export USE_CACHE=true

# Or use faster index type
python scripts/build_vector_db.py --index-type hnsw
```

## Next Steps

1. **Customize with your data**
   - Add your product images to `data/images/`
   - Create `data/metadata.csv` with your products
   - Rebuild embeddings and index

2. **Deploy to production**
   - See [DEPLOYMENT.md](DEPLOYMENT.md)
   - Use Docker or Kubernetes
   - Configure monitoring

3. **Extend functionality**
   - Add more filters
   - Implement user feedback
   - Customize UI theme
   - Add authentication

## Performance Tips

### For Development
- Use sample dataset (100-1000 products)
- Use Flat FAISS index
- Disable reranking
- Use ViT-B-32 model

### For Production
- Use real dataset (10K+ products)
- Use HNSW/IVF index for >10K products
- Enable Redis caching
- Consider GPU for encoding
- Use ViT-B-16 or ViT-L-14 for better accuracy

## Resources

- **API Documentation**: http://localhost:8000/docs
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Advanced Features**: [README_ADVANCED.md](README_ADVANCED.md)

## Getting Help

- Check [Troubleshooting](#troubleshooting) section
- Read [ARCHITECTURE.md](ARCHITECTURE.md) for system details
- Open an issue on GitHub
- Check existing issues and discussions

---

**Ready to search!** 🎉
