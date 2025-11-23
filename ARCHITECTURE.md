# Architecture Documentation

## System Overview

The Multi-Modal Retail Assistant is a full-stack application that enables semantic search across product catalogs using both visual and textual queries. It leverages CLIP (Contrastive Language-Image Pre-training) for multi-modal embeddings and FAISS for efficient similarity search.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                           │
│                    (Streamlit Frontend)                          │
│                         Port 8501                                │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API                                 │
│                    (FastAPI Service)                             │
│                        Port 8000                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌─────────────────┐            ┌──────────────────┐
│  CLIP Encoder   │            │  Vector Database │
│ (SentenceTransf)│            │     (FAISS)      │
└─────────────────┘            └──────────────────┘
         │                               │
         │                               │
         ▼                               ▼
┌─────────────────────────────────────────────────┐
│              Product Catalog                     │
│         (Images + Metadata)                      │
└─────────────────────────────────────────────────┘
```

## Component Details

### 1. Frontend Layer (Streamlit)

**Location:** `frontend/app.py`

**Responsibilities:**
- Render user interface
- Handle file uploads
- Make API requests to backend
- Display search results in grid layout
- Manage user settings (k, search mode)

**Technologies:**
- Streamlit 1.28+
- Requests library for HTTP
- PIL for image display

**Key Features:**
- Image upload interface
- Text query input
- Real-time search
- Grid-based result display
- Similarity score visualization

### 2. Backend Layer (FastAPI)

**Location:** `backend/main.py`, `backend/search_engine.py`

**Responsibilities:**
- Expose REST API endpoints
- Process search requests
- Encode queries using CLIP
- Query vector database
- Return formatted results

**Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/health` | GET | System status |
| `/search/image` | POST | Image similarity search |
| `/search/text` | POST | Text similarity search |
| `/products/{id}` | GET | Get product details |
| `/categories` | GET | List categories |

**Technologies:**
- FastAPI 0.104+
- Uvicorn (ASGI server)
- Pydantic (data validation)

### 3. Embedding Layer (CLIP)

**Location:** `scripts/build_embeddings.py`

**Responsibilities:**
- Load pre-trained CLIP model
- Encode images to 512-dim vectors
- Encode text to 512-dim vectors
- Batch processing for efficiency
- Maintain embedding consistency

**Model Architecture:**
```
CLIP Model (clip-ViT-B-32)
    ├── Vision Transformer (ViT-B/32)
    │   ├── Patch Embedding
    │   ├── Transformer Blocks (12 layers)
    │   └── Projection Head → 512-dim
    │
    └── Text Transformer
        ├── Token Embedding
        ├── Transformer Blocks (12 layers)
        └── Projection Head → 512-dim
```

**Process:**
1. Input: Image (RGB) or Text (string)
2. Preprocessing: Resize/normalize or tokenize
3. Forward pass through model
4. L2 normalization
5. Output: 512-dim embedding vector

### 4. Vector Database Layer (FAISS)

**Location:** `scripts/build_vector_db.py`

**Responsibilities:**
- Store embedding vectors
- Perform k-nearest neighbor search
- Support multiple index types
- Fast similarity computation

**Index Types:**

| Type | Best For | Speed | Accuracy |
|------|----------|-------|----------|
| Flat | <10K products | Medium | 100% |
| IVF | 10K-1M products | Fast | ~95% |
| HNSW | >100K products | Very Fast | ~99% |

**Search Algorithm:**
```python
def search(query_vector, k=5):
    1. Normalize query vector (L2)
    2. Compute cosine similarity with all vectors
    3. Return top-k indices and distances
    4. Map indices to product metadata
    5. Calculate similarity scores
```

### 5. Data Layer

**Structure:**
```
data/
├── images/               # Product images (JPG/PNG)
├── embeddings/
│   ├── image_embeddings.npy      # (N, 512) array
│   ├── text_embeddings.npy       # (N, 512) array
│   └── metadata_with_embeddings.csv
└── vector_db/
    ├── image_index.faiss         # FAISS index for images
    ├── text_index.faiss          # FAISS index for text
    ├── metadata.csv              # Product metadata
    └── db_config.pkl             # Configuration
```

## Data Flow

### Image Search Flow

```
1. User uploads image → Frontend
2. Frontend sends image → Backend API (/search/image)
3. Backend:
   a. Load image with PIL
   b. Encode with CLIP → 512-dim vector
   c. Normalize vector (L2)
   d. Query FAISS image index
   e. Get top-k indices and distances
   f. Map to product metadata
   g. Calculate similarity scores
4. Backend returns JSON results
5. Frontend displays products in grid
```

### Text Search Flow

```
1. User enters query → Frontend
2. Frontend sends text → Backend API (/search/text)
3. Backend:
   a. Encode text with CLIP → 512-dim vector
   b. Normalize vector (L2)
   c. Query FAISS text index
   d. Get top-k indices and distances
   e. Map to product metadata
   f. Calculate similarity scores
4. Backend returns JSON results
5. Frontend displays products in grid
```

### Cross-Modal Search

The system supports cross-modal retrieval:
- **Text-to-Image**: Query with text, search in image index
- **Image-to-Text**: Query with image, search in text index

This is possible because CLIP aligns image and text embeddings in the same vector space.

## Embedding Pipeline

```
Data Preparation Pipeline:
────────────────────────
1. Collect product images + metadata
2. Organize in data/ directory
3. Run download_dataset.py → metadata.csv

Embedding Generation:
────────────────────
4. Run build_embeddings.py
   ├── Load CLIP model
   ├── For each product:
   │   ├── Load image
   │   ├── Encode → image_embedding
   │   ├── Combine title + description
   │   └── Encode → text_embedding
   ├── Save embeddings as .npy arrays
   └── Update metadata CSV

Index Building:
──────────────
5. Run build_vector_db.py
   ├── Load embeddings
   ├── Create FAISS indexes
   ├── Add vectors to indexes
   └── Save indexes to disk

Ready for Search!
```

## Search Modes

### 1. Image-to-Image (Default)
- Query: Image
- Search In: Image index
- Use Case: "Find visually similar products"

### 2. Text-to-Text
- Query: Text
- Search In: Text index
- Use Case: "Find products with similar descriptions"

### 3. Text-to-Image (Cross-Modal)
- Query: Text
- Search In: Image index
- Use Case: "Show me what a red dress looks like"

### 4. Image-to-Text (Cross-Modal)
- Query: Image
- Search In: Text index
- Use Case: "Find products described like this image"

## Similarity Scoring

```python
# FAISS returns L2 distances
distance = L2(query_vector, product_vector)

# Convert to similarity score (0-1)
similarity = 1 / (1 + distance)

# After L2 normalization, L2 distance relates to cosine similarity:
# cosine_similarity = 1 - (L2_distance^2 / 2)
```

## Performance Characteristics

### Latency Breakdown (typical)

```
Total Search Time: ~100ms
├── Image Upload: ~10ms (frontend → backend)
├── CLIP Encoding: ~50ms (CPU) / ~10ms (GPU)
├── FAISS Search: ~5ms (flat) / ~1ms (IVF/HNSW)
├── Metadata Lookup: ~5ms
└── JSON Serialization: ~5ms
```

### Scalability

| Products | Index Type | Memory | Search Time | Build Time |
|----------|-----------|--------|-------------|------------|
| 1K | Flat | ~2MB | <5ms | <1s |
| 10K | Flat | ~20MB | ~10ms | ~5s |
| 100K | IVF | ~200MB | ~5ms | ~30s |
| 1M | HNSW | ~2GB | ~10ms | ~5min |

### Optimization Strategies

1. **GPU Acceleration**
   - Use CUDA for CLIP encoding
   - 10x faster embedding generation

2. **Batch Processing**
   - Process multiple queries together
   - Reduce model loading overhead

3. **Index Optimization**
   - Use IVF for 10K+ products
   - Use HNSW for 100K+ products

4. **Caching**
   - Cache frequent queries
   - Use Redis for distributed cache

5. **Quantization**
   - Reduce embedding precision
   - 4x memory reduction

## Deployment Architectures

### Development (Local)
```
Developer Machine
├── Backend (localhost:8000)
└── Frontend (localhost:8501)
```

### Production (Docker)
```
Docker Host
├── Container: retail-assistant-backend
│   ├── FastAPI app
│   ├── CLIP model
│   └── FAISS indexes
│
└── Container: retail-assistant-frontend
    └── Streamlit app
```

### Production (Cloud)
```
Load Balancer
    │
    ├── Backend Instances (3x)
    │   ├── Auto-scaling
    │   ├── Health checks
    │   └── Shared vector DB
    │
    ├── Frontend Instances (2x)
    │
    └── Shared Storage
        └── Vector Database (NFS/S3)
```

## Security Considerations

1. **Input Validation**
   - File type checking
   - Size limits (max 10MB)
   - Image format validation

2. **Rate Limiting**
   - Max requests per IP
   - Prevent abuse

3. **API Authentication** (optional)
   - JWT tokens
   - API keys

4. **Data Privacy**
   - No query logging (optional)
   - Encrypted storage

## Monitoring & Logging

**Metrics to Track:**
- Search latency (p50, p95, p99)
- Encoding time
- FAISS search time
- Error rates
- Cache hit rates
- API request counts

**Logging:**
- Structured JSON logs
- Request/response logging
- Error tracking
- Performance metrics

## Future Enhancements

1. **Hybrid Search**
   - Combine image + text queries
   - Weighted fusion of results

2. **Re-ranking**
   - Use cross-encoder for re-ranking
   - Improve top-5 accuracy

3. **Personalization**
   - User preference learning
   - Query history analysis

4. **Multi-modal Fusion**
   - Combine multiple images
   - Contextual text queries

5. **Advanced Filtering**
   - Price range
   - Brand filtering
   - Availability status

---

**Last Updated:** 2025-11-23
