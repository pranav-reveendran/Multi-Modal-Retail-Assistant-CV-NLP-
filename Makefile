.PHONY: help install data embeddings vector-db backend frontend docker-build docker-up docker-down clean test

help:
	@echo "Multi-Modal Retail Assistant - Make Commands"
	@echo "============================================="
	@echo ""
	@echo "Setup:"
	@echo "  make install      - Install dependencies"
	@echo "  make data         - Generate sample dataset"
	@echo "  make embeddings   - Build CLIP embeddings"
	@echo "  make vector-db    - Build FAISS vector database"
	@echo "  make setup        - Run complete setup (install + data + embeddings + vector-db)"
	@echo ""
	@echo "Development:"
	@echo "  make backend      - Start FastAPI backend"
	@echo "  make frontend     - Start Streamlit frontend"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build - Build Docker images"
	@echo "  make docker-up    - Start containers"
	@echo "  make docker-down  - Stop containers"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean        - Clean generated files"
	@echo "  make test         - Run tests"

install:
	pip install -r requirements.txt

data:
	python scripts/download_dataset.py --num-samples 100 --placeholder

embeddings:
	python scripts/build_embeddings.py --metadata data/metadata.csv --output data/embeddings

vector-db:
	python scripts/build_vector_db.py --embeddings-dir data/embeddings --output-dir data/vector_db

setup: install data embeddings vector-db
	@echo "✅ Setup complete!"

backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:
	streamlit run frontend/app.py

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	rm -rf data/images/* data/embeddings/* data/vector_db/*
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	pytest tests/ -v
