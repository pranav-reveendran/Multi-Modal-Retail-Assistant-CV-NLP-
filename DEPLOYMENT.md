# Deployment Guide

This guide covers deploying the Multi-Modal Retail Assistant to various platforms.

## Table of Contents
- [Quick Start (Local)](#quick-start-local)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [AWS Deployment](#aws-deployment)
- [GCP Deployment](#gcp-deployment)
- [Azure Deployment](#azure-deployment)
- [Production Considerations](#production-considerations)

## Quick Start (Local)

### Prerequisites
- Python 3.10+
- 8GB+ RAM
- ~10GB disk space

### Steps

1. **Setup Environment**
```bash
# Clone repository
git clone <repository-url>
cd Multi-Modal-Retail-Assistant-CV-NLP-

# Run automated setup
./setup.sh
```

2. **Download Real Dataset**
```bash
# Configure Kaggle API (one-time setup)
# Get API key from https://www.kaggle.com/settings/account
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Download Fashion Product Images dataset (44K products)
python scripts/download_real_dataset.py --dataset fashion

# OR download Amazon products
python scripts/download_real_dataset.py --dataset amazon
```

3. **Build Embeddings & Vector Database**
```bash
# Generate CLIP embeddings (~10-30 minutes depending on dataset size)
python scripts/build_embeddings.py

# Build FAISS index
python scripts/build_vector_db.py
```

4. **Start Application**
```bash
# Terminal 1: Backend
uvicorn backend.main_advanced:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Frontend
streamlit run frontend/app_advanced.py
```

5. **Access Application**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000/docs

## Docker Deployment

### Basic Deployment

```bash
# Build and start containers
docker-compose up --build

# Access at:
# - Frontend: http://localhost:8501
# - Backend: http://localhost:8000
```

### Advanced Deployment (with Redis)

```bash
# Use advanced compose file with caching
docker-compose -f docker-compose-advanced.yml up --build

# Features:
# - Redis caching for faster queries
# - Resource limits
# - Health checks
# - Automatic restarts
```

### Production Docker Tips

1. **Use multi-stage builds** (already implemented in Dockerfiles)

2. **Optimize image size**:
```bash
# Remove unnecessary files
docker image prune -a

# Use slim base images (already using python:3.10-slim)
```

3. **Security**:
```bash
# Scan images for vulnerabilities
docker scan retail-assistant-backend:latest
docker scan retail-assistant-frontend:latest
```

4. **Monitoring**:
```bash
# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Monitor resources
docker stats
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Persistent storage provisioner
- (Optional) NGINX Ingress Controller
- (Optional) cert-manager for TLS

### Deployment Steps

1. **Create Namespace**
```bash
kubectl create namespace retail-assistant
kubectl config set-context --current --namespace=retail-assistant
```

2. **Deploy Persistent Storage**
```bash
kubectl apply -f deploy/kubernetes/pvc.yaml
```

3. **Upload Data to PVC**
```bash
# Create a temporary pod to upload data
kubectl run data-uploader --image=busybox --restart=Never -- sleep 3600

# Copy data
kubectl cp data/ data-uploader:/data/

# Delete temporary pod
kubectl delete pod data-uploader
```

4. **Deploy Services**
```bash
# Deploy Redis, Backend, and Frontend
kubectl apply -f deploy/kubernetes/deployment.yaml

# Create services
kubectl apply -f deploy/kubernetes/service.yaml

# Configure autoscaling
kubectl apply -f deploy/kubernetes/hpa.yaml

# Set up ingress (update domain in file first)
kubectl apply -f deploy/kubernetes/ingress.yaml
```

5. **Verify Deployment**
```bash
# Check pods
kubectl get pods

# Check services
kubectl get svc

# View logs
kubectl logs -f deployment/retail-assistant-backend

# Test backend
kubectl port-forward svc/retail-assistant-backend 8000:8000
```

6. **Access Application**
```bash
# Get frontend URL
kubectl get svc retail-assistant-frontend

# Or use ingress
# https://retail-assistant.yourdomain.com
```

### Scaling

```bash
# Manual scaling
kubectl scale deployment retail-assistant-backend --replicas=5

# HPA automatically scales based on CPU/memory
# Check HPA status
kubectl get hpa
```

### Monitoring

```bash
# Install Prometheus & Grafana (if not already)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack

# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80
# Default: admin/prom-operator
```

## AWS Deployment

### Option 1: AWS ECS Fargate (Recommended for simplicity)

1. **Prerequisites**
```bash
# Install AWS CLI
aws configure

# Set variables
export AWS_REGION=us-east-1
export CLUSTER_NAME=retail-assistant-cluster
```

2. **Run Deployment Script**
```bash
cd deploy/aws
chmod +x deploy.sh
./deploy.sh
```

3. **Manual Steps** (if script fails)
```bash
# Create ECR repositories
aws ecr create-repository --repository-name retail-assistant-backend
aws ecr create-repository --repository-name retail-assistant-frontend

# Build and push images
$(aws ecr get-login --no-include-email)
docker build -f Dockerfile.backend -t <ecr-uri>/retail-assistant-backend:latest .
docker push <ecr-uri>/retail-assistant-backend:latest

# Create ECS cluster
aws ecs create-cluster --cluster-name retail-assistant-cluster

# Register task definitions
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# Create services
aws ecs create-service \
  --cluster retail-assistant-cluster \
  --service-name retail-assistant-backend \
  --task-definition retail-assistant-backend \
  --desired-count 3 \
  --launch-type FARGATE
```

4. **Set up Load Balancer**
```bash
# Create Application Load Balancer
aws elbv2 create-load-balancer \
  --name retail-assistant-alb \
  --subnets subnet-xxx subnet-yyy \
  --security-groups sg-xxx

# Create target group and listeners
# Configure Auto Scaling
```

### Option 2: AWS EKS (for advanced use)

```bash
# Create EKS cluster
eksctl create cluster \
  --name retail-assistant \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type m5.xlarge \
  --nodes 3

# Configure kubectl
aws eks update-kubeconfig --name retail-assistant

# Deploy using Kubernetes manifests
kubectl apply -f deploy/kubernetes/
```

### AWS Services to Consider

- **EFS**: For shared data storage
- **ElastiCache**: For Redis caching
- **CloudWatch**: For monitoring and logging
- **Route 53**: For DNS management
- **CloudFront**: For CDN
- **S3**: For image storage

## GCP Deployment

### Option 1: Cloud Run (Recommended for simplicity)

1. **Prerequisites**
```bash
# Install gcloud CLI
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. **Run Deployment Script**
```bash
cd deploy/gcp
chmod +x deploy.sh
export GCP_PROJECT_ID=your-project-id
./deploy.sh
```

3. **Manual Deployment**
```bash
# Build images
gcloud builds submit --tag gcr.io/PROJECT_ID/retail-assistant-backend .

# Deploy to Cloud Run
gcloud run deploy retail-assistant-backend \
  --image gcr.io/PROJECT_ID/retail-assistant-backend \
  --platform managed \
  --region us-central1 \
  --memory 8Gi \
  --cpu 4 \
  --allow-unauthenticated
```

### Option 2: GKE (for advanced use)

```bash
# Create GKE cluster
gcloud container clusters create retail-assistant \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-4

# Get credentials
gcloud container clusters get-credentials retail-assistant

# Deploy
kubectl apply -f deploy/kubernetes/
```

### GCP Services to Consider

- **Cloud Storage**: For images
- **Memorystore**: For Redis
- **Cloud CDN**: For content delivery
- **Cloud Monitoring**: For observability
- **Cloud Load Balancing**: For traffic management

## Azure Deployment

### Option 1: Azure Container Instances (Simple)

1. **Prerequisites**
```bash
# Install Azure CLI
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

2. **Run Deployment Script**
```bash
cd deploy/azure
chmod +x deploy.sh
export AZURE_RESOURCE_GROUP=retail-assistant-rg
./deploy.sh
```

### Option 2: AKS (Production)

```bash
# Create AKS cluster
az aks create \
  --resource-group retail-assistant-rg \
  --name retail-assistant-aks \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-addons monitoring

# Get credentials
az aks get-credentials --resource-group retail-assistant-rg --name retail-assistant-aks

# Deploy
kubectl apply -f deploy/kubernetes/
```

### Azure Services to Consider

- **Azure Files**: For shared storage
- **Azure Cache for Redis**: For caching
- **Azure CDN**: For content delivery
- **Azure Monitor**: For observability
- **Application Gateway**: For load balancing

## Production Considerations

### Performance Optimization

1. **Use GPU for encoding** (10x faster):
```dockerfile
# Update Dockerfile to use CUDA base image
FROM nvidia/cuda:11.8.0-cudask-ubuntu22.04

# Install torch with CUDA
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

2. **Enable caching**:
```bash
# Deploy Redis
docker run -d -p 6379:6379 redis:7-alpine

# Enable in backend
export USE_CACHE=true
export REDIS_HOST=redis-host
```

3. **Use efficient FAISS index**:
```python
# For >100K products, use IVF or HNSW
python scripts/build_vector_db.py --index-type hnsw
```

### Security

1. **Enable HTTPS**:
```bash
# Kubernetes: Use cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Configure Let's Encrypt issuer
# Update ingress.yaml with TLS configuration
```

2. **Add authentication**:
```python
# Add OAuth2/JWT to FastAPI
from fastapi.security import OAuth2PasswordBearer
```

3. **Secure secrets**:
```bash
# Kubernetes: Use secrets
kubectl create secret generic redis-password --from-literal=password=YOUR_PASSWORD

# AWS: Use Secrets Manager
# GCP: Use Secret Manager
# Azure: Use Key Vault
```

### Monitoring

1. **Application Performance Monitoring (APM)**:
```python
# Add Datadog, New Relic, or App Insights
```

2. **Logging**:
```bash
# Kubernetes: ELK Stack or Loki
# AWS: CloudWatch
# GCP: Cloud Logging
# Azure: Azure Monitor
```

3. **Metrics**:
- Query latency (p50, p95, p99)
- Cache hit rate
- Error rates
- Resource utilization

### Backup & Recovery

1. **Data Backup**:
```bash
# Regular backups of vector database and metadata
tar -czf backup-$(date +%Y%m%d).tar.gz data/
aws s3 cp backup-*.tar.gz s3://your-backup-bucket/
```

2. **Disaster Recovery**:
- Multi-region deployment
- Automated failover
- Regular restore testing

### Cost Optimization

1. **Right-size resources**:
- Start small and scale based on metrics
- Use autoscaling
- Consider spot/preemptible instances

2. **Optimize storage**:
- Use object storage (S3/GCS) for images
- Compress embeddings
- Clean up old data

3. **Use caching**:
- Reduces API calls
- Improves response time
- Lowers compute costs

## Troubleshooting

### Common Issues

1. **Out of Memory**:
```bash
# Increase container memory
# Use smaller CLIP model
# Process data in batches
```

2. **Slow Search**:
```bash
# Enable caching
# Use HNSW index
# Add more replicas
```

3. **Failed Health Checks**:
```bash
# Check logs
kubectl logs pod-name
# Increase startup time
# Verify environment variables
```

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: README.md, ARCHITECTURE.md
- Community: [Discord/Slack link]

---

**Last Updated**: 2025-11-23
