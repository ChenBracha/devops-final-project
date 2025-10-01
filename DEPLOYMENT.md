# 🚀 Deployment Guide

This project supports **two deployment methods** that can run **simultaneously** on different ports!

## 📋 Quick Start

Run the deployment script:
```bash
python3 deploy.py
# or
./deploy.sh
```

## 🎯 Deployment Options

### 1. 🐳 Docker Compose (Port 8887)
- **Best for**: Local development, quick testing
- **URL**: http://localhost:8887
- **Setup time**: ~2 minutes
- **Requirements**: Docker, Docker Compose

**Features:**
- Simple single-command deployment
- Easy to start/stop
- Perfect for development

### 2. ☸️  Kubernetes with K3d (Port 8889)
- **Best for**: Learning Kubernetes, production-like setup
- **URL**: http://localhost:8889
- **Setup time**: ~5 minutes
- **Requirements**: Docker, kubectl, k3d

**Features:**
- Production-like environment
- Kubernetes manifest practice
- Scalable architecture
- Separate namespaces and secrets

## 💡 Running Both Simultaneously

**Yes, you can run both at the same time!** They use different ports:
- Docker Compose: `localhost:8887`
- Kubernetes: `localhost:8889`

This is useful for:
- Comparing performance
- Testing different configurations
- Learning differences between Docker Compose and Kubernetes

## 🔄 Switching Between Deployments

The deployment script automatically:
1. ✅ Detects which services are running
2. ✅ Asks if you want to stop them
3. ✅ Handles port conflicts gracefully
4. ✅ Starts Docker Desktop if needed (macOS)

### Example Flow:

```bash
$ python3 deploy.py

🔍 Checking Docker Desktop...
✅ Docker is running

Choose your deployment method:
1. 🐳 Docker Compose → http://localhost:8887
2. ☸️  Kubernetes → http://localhost:8889

💡 TIP: You can run both simultaneously on different ports!

👉 Choose deployment method (1 or 2):
```

## 🛠️ Manual Deployment

### Docker Compose
```bash
docker-compose up -d
# Access at http://localhost:8887
```

### Kubernetes
```bash
# Create cluster
k3d cluster create budget-cluster --port "8889:80@loadbalancer"

# Deploy
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/flask-app/
kubectl apply -f k8s/nginx/

# Port forward
kubectl port-forward service/nginx-service 8889:80 -n budget-app
# Access at http://localhost:8889
```

## 🛑 Stopping Services

### Docker Compose
```bash
docker-compose down
```

### Kubernetes
```bash
# Stop port-forward
pkill -f "kubectl.*port-forward"

# Delete cluster (optional)
k3d cluster delete budget-cluster
```

## 📊 Port Summary

| Deployment       | Port | URL                        |
|------------------|------|----------------------------|
| Docker Compose   | 8887 | http://localhost:8887      |
| Kubernetes (K3d) | 8889 | http://localhost:8889      |

## 🔍 Troubleshooting

### Port Already in Use
The script will detect this and offer to stop the existing service.

### Docker Not Running
The script will offer to start Docker Desktop automatically (macOS).

### Can't Switch Deployments
Make sure to stop the current deployment first, or choose a different port.

## 📚 Learn More

- Docker Compose: Simple, file-based orchestration
- Kubernetes: Industry-standard container orchestration
- K3d: Lightweight Kubernetes in Docker (perfect for local development) 