#!/bin/bash

# Multi-Modal Retail Assistant Setup Script
# This script automates the setup process

set -e  # Exit on error

echo "🛍️  Multi-Modal Retail Assistant Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
echo ""
echo "Creating data directories..."
mkdir -p data/images data/embeddings data/vector_db

# Download sample dataset
echo ""
read -p "Do you want to generate a sample dataset? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    read -p "Number of samples (default: 100): " num_samples
    num_samples=${num_samples:-100}

    echo "Generating sample dataset with $num_samples products..."
    python scripts/download_dataset.py --num-samples $num_samples --placeholder
fi

# Build embeddings
echo ""
read -p "Do you want to build embeddings now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    if [ -f "data/metadata.csv" ]; then
        echo "Building embeddings..."
        python scripts/build_embeddings.py --metadata data/metadata.csv --output data/embeddings

        echo ""
        echo "Building vector database..."
        python scripts/build_vector_db.py --embeddings-dir data/embeddings --output-dir data/vector_db
    else
        echo "⚠️  metadata.csv not found. Please generate dataset first."
    fi
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Start backend: cd backend && uvicorn main:app --reload"
echo "  3. Start frontend (in new terminal): streamlit run frontend/app.py"
echo ""
echo "Or use Docker:"
echo "  docker-compose up --build"
echo ""
