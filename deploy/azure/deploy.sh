#!/bin/bash

# Azure Deployment Script for Multi-Modal Retail Assistant
# Deploys to Azure Container Instances or AKS

set -e

echo "🚀 Deploying Multi-Modal Retail Assistant to Azure"
echo "===================================================="

# Configuration
RESOURCE_GROUP=${AZURE_RESOURCE_GROUP:-retail-assistant-rg}
LOCATION=${AZURE_LOCATION:-eastus}
ACR_NAME=${AZURE_ACR_NAME:-retailassistantacr}
BACKEND_IMAGE="retail-assistant-backend"
FRONTEND_IMAGE="retail-assistant-frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Step 1: Creating resource group${NC}"
az group create --name $RESOURCE_GROUP --location $LOCATION

echo -e "${BLUE}Step 2: Creating Azure Container Registry${NC}"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $ACR_NAME \
    --sku Standard \
    --admin-enabled true

echo -e "${GREEN}✓ ACR created${NC}"

echo -e "${BLUE}Step 3: Building and pushing images${NC}"

cd ../..

# Login to ACR
az acr login --name $ACR_NAME

# Build and push backend
az acr build \
    --registry $ACR_NAME \
    --image $BACKEND_IMAGE:latest \
    --file Dockerfile.backend \
    .

# Build and push frontend
az acr build \
    --registry $ACR_NAME \
    --image $FRONTEND_IMAGE:latest \
    --file Dockerfile.frontend \
    .

echo -e "${GREEN}✓ Images built and pushed${NC}"

echo -e "${BLUE}Step 4: Creating Azure Container Instances${NC}"

# Get ACR credentials
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer --output tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" --output tsv)

# Deploy backend
az container create \
    --resource-group $RESOURCE_GROUP \
    --name retail-assistant-backend \
    --image $ACR_LOGIN_SERVER/$BACKEND_IMAGE:latest \
    --registry-username $ACR_NAME \
    --registry-password $ACR_PASSWORD \
    --cpu 4 \
    --memory 8 \
    --ip-address Public \
    --ports 8000 \
    --environment-variables \
        VECTOR_DB_PATH=/data/vector_db \
        CLIP_MODEL_NAME=clip-ViT-B-32 \
        USE_CACHE=true

# Get backend IP
BACKEND_IP=$(az container show --resource-group $RESOURCE_GROUP --name retail-assistant-backend --query ipAddress.ip --output tsv)

echo -e "${GREEN}✓ Backend deployed at $BACKEND_IP${NC}"

# Deploy frontend
az container create \
    --resource-group $RESOURCE_GROUP \
    --name retail-assistant-frontend \
    --image $ACR_LOGIN_SERVER/$FRONTEND_IMAGE:latest \
    --registry-username $ACR_NAME \
    --registry-password $ACR_PASSWORD \
    --cpu 1 \
    --memory 2 \
    --ip-address Public \
    --ports 8501 \
    --environment-variables \
        API_URL=http://$BACKEND_IP:8000

FRONTEND_IP=$(az container show --resource-group $RESOURCE_GROUP --name retail-assistant-frontend --query ipAddress.ip --output tsv)

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Access your application:"
echo "  Frontend: http://$FRONTEND_IP:8501"
echo "  Backend API: http://$BACKEND_IP:8000"
echo ""
echo "Next steps:"
echo "  1. Configure Azure Application Gateway"
echo "  2. Set up Azure Front Door for CDN"
echo "  3. Configure Azure Monitor"
echo "  4. Set up Azure Cache for Redis (if needed)"
echo "  5. Consider migrating to AKS for production"
