#!/bin/bash

# GCP Deployment Script for Multi-Modal Retail Assistant
# Deploys to Google Cloud Run or GKE

set -e

echo "🚀 Deploying Multi-Modal Retail Assistant to GCP"
echo "================================================="

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-your-project-id}
REGION=${GCP_REGION:-us-central1}
SERVICE_NAME="retail-assistant"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Enabling required APIs${NC}"
gcloud services enable \
    run.googleapis.com \
    containerregistry.googleapis.com \
    cloudbuild.googleapis.com \
    --project=$PROJECT_ID

echo -e "${BLUE}Step 2: Building images with Cloud Build${NC}"

cd ../..

# Build backend
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/retail-assistant-backend:latest \
    --file Dockerfile.backend \
    --project=$PROJECT_ID \
    .

# Build frontend
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/retail-assistant-frontend:latest \
    --file Dockerfile.frontend \
    --project=$PROJECT_ID \
    .

echo -e "${GREEN}✓ Images built and pushed to GCR${NC}"

echo -e "${BLUE}Step 3: Deploying to Cloud Run${NC}"

# Deploy backend
gcloud run deploy retail-assistant-backend \
    --image gcr.io/$PROJECT_ID/retail-assistant-backend:latest \
    --platform managed \
    --region $REGION \
    --memory 8Gi \
    --cpu 4 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars VECTOR_DB_PATH=/data/vector_db,CLIP_MODEL_NAME=clip-ViT-B-32,USE_CACHE=true \
    --allow-unauthenticated \
    --project=$PROJECT_ID

# Get backend URL
BACKEND_URL=$(gcloud run services describe retail-assistant-backend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

echo -e "${GREEN}✓ Backend deployed: $BACKEND_URL${NC}"

# Deploy frontend
gcloud run deploy retail-assistant-frontend \
    --image gcr.io/$PROJECT_ID/retail-assistant-frontend:latest \
    --platform managed \
    --region $REGION \
    --memory 2Gi \
    --cpu 1 \
    --min-instances 1 \
    --max-instances 5 \
    --set-env-vars API_URL=$BACKEND_URL \
    --allow-unauthenticated \
    --project=$PROJECT_ID

FRONTEND_URL=$(gcloud run services describe retail-assistant-frontend --region=$REGION --format='value(status.url)' --project=$PROJECT_ID)

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Access your application:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend API: $BACKEND_URL"
echo ""
echo "Next steps:"
echo "  1. Configure custom domain"
echo "  2. Set up Cloud CDN"
echo "  3. Configure Cloud Monitoring"
echo "  4. Set up Memorystore for Redis (if needed)"
