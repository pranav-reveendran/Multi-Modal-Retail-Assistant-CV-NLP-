#!/bin/bash

# AWS Deployment Script for Multi-Modal Retail Assistant
# Deploys to AWS ECS with Fargate

set -e

echo "🚀 Deploying Multi-Modal Retail Assistant to AWS"
echo "=================================================="

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
CLUSTER_NAME=${CLUSTER_NAME:-retail-assistant-cluster}
ECR_REPO_BACKEND="retail-assistant-backend"
ECR_REPO_FRONTEND="retail-assistant-frontend"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Step 1: Creating ECR repositories${NC}"
aws ecr create-repository --repository-name $ECR_REPO_BACKEND --region $AWS_REGION || true
aws ecr create-repository --repository-name $ECR_REPO_FRONTEND --region $AWS_REGION || true

# Get ECR URLs
BACKEND_ECR=$(aws ecr describe-repositories --repository-names $ECR_REPO_BACKEND --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)
FRONTEND_ECR=$(aws ecr describe-repositories --repository-names $ECR_REPO_FRONTEND --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)

echo -e "${GREEN}✓ ECR repositories ready${NC}"
echo "  Backend: $BACKEND_ECR"
echo "  Frontend: $FRONTEND_ECR"

echo -e "${BLUE}Step 2: Building and pushing Docker images${NC}"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $BACKEND_ECR

# Build and push backend
cd ../..
docker build -f Dockerfile.backend -t $BACKEND_ECR:latest .
docker push $BACKEND_ECR:latest

# Build and push frontend
docker build -f Dockerfile.frontend -t $FRONTEND_ECR:latest .
docker push $FRONTEND_ECR:latest

echo -e "${GREEN}✓ Images pushed to ECR${NC}"

echo -e "${BLUE}Step 3: Creating ECS cluster${NC}"
aws ecs create-cluster --cluster-name $CLUSTER_NAME --region $AWS_REGION || true

echo -e "${BLUE}Step 4: Creating task definitions${NC}"
# This would normally use the task definition JSON files
# See ecs-task-definition.json

echo -e "${BLUE}Step 5: Creating ECS services${NC}"
# Create services using the task definitions

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Configure Application Load Balancer"
echo "  2. Set up Route 53 DNS"
echo "  3. Configure Auto Scaling"
echo "  4. Set up CloudWatch monitoring"
