# 🚀 Deployment Workflow

## Overview

This project uses **Continuous Integration (CI)** via GitHub Actions and **manual local deployment** for development and testing.

```
┌─────────────────────────────────────────────────────────────┐
│                  Development Workflow                        │
└─────────────────────────────────────────────────────────────┘

1. Code Changes (Local)
   ↓
2. Git Push to GitHub
   ↓
3. CI Pipeline (Automated)
   ├── Build Docker images
   ├── Run tests
   ├── Security scan (Trivy)
   └── ✅ Pass / ❌ Fail
   ↓
4. Manual Deployment (Local)
   ├── Option A: Docker Compose (quick dev)
   └── Option B: K3d (production-like)
```

---

## 🔄 Continuous Integration (CI)

**Automated on every push to any branch**

### What Happens:
1. **Checkout code** from GitHub
2. **Build Docker images** (web, nginx)
3. **Run linting** (code quality checks)
4. **Security scan** with Trivy (critical vulnerabilities only)
5. **Upload artifacts** (build outputs)

### Status:
- ✅ **Workflow file:** `.github/workflows/ci.yml`
- ✅ **Triggered on:** Push to any branch, Pull requests
- ✅ **Results:** Visible in GitHub Actions tab

### View CI Status:
```bash
# Check latest CI run
https://github.com/YOUR_USERNAME/devops-final-project/actions
```

---

## 📦 Continuous Deployment (CD)

**Manual deployment to local environments**

Since both Docker Compose and K3d run locally on your laptop, deployment is manual. 

> **Note:** In a production environment, CD would be fully automated using:
> - GitOps tools (ArgoCD, FluxCD)
> - GitHub Actions with self-hosted runners
> - Cloud-native CD pipelines (GCP Cloud Build, AWS CodePipeline)
> - Deployment to remote Kubernetes clusters

For local development, manual deployment is the standard practice. Here's the workflow:

### Step 1: Ensure CI Passed ✅
```bash
# Check GitHub Actions
# Green checkmark on your commit = good to deploy
```

### Step 2: Pull Latest Code
```bash
git pull origin main
```

### Step 3: Rebuild Images (if code changed)
```bash
# Rebuild Docker images with latest code
docker-compose build --no-cache
```

### Step 4: Choose Deployment Method

#### Option A: Docker Compose (Quick Development)
```bash
# Using deployment script
python3 deploy.py
# Choose option 1

# Or manually
docker-compose down
docker-compose build
docker-compose up -d

# Access at http://localhost:8887
```

**When to use:**
- 🚀 Quick feature testing
- 🔧 Rapid iteration
- 🐛 Debugging

#### Option B: K3d (Production-like)
```bash
# Using deployment script
python3 deploy.py
# Choose option 2

# Or manually
k3d cluster create budget-cluster --port "8889:80@loadbalancer"
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/flask-app/
kubectl apply -f k8s/nginx/
kubectl apply -f k8s/monitoring/

# Access at http://localhost:8889
```

**When to use:**
- ✅ Testing K8s configurations
- 📊 Testing with monitoring stack
- 🎓 Learning Kubernetes
- 🎯 Pre-demo verification

---

## 🎯 Deployment Decision Tree

```
Need quick test of code changes?
├─ YES → Use Docker Compose (faster)
└─ NO  → Continue...

Testing Kubernetes configs?
├─ YES → Use K3d
└─ NO  → Continue...

Need monitoring/metrics?
├─ YES → Use K3d (has Prometheus/Grafana)
└─ NO  → Use Docker Compose

Preparing for demo/presentation?
└─ Use K3d (production-like)
```

---

## 📋 Pre-Deployment Checklist

Before deploying, verify:

- [ ] ✅ CI pipeline passed (green checkmark on GitHub)
- [ ] 📝 Environment variables set (`.env` file exists)
- [ ] 🐳 Docker Desktop is running
- [ ] 🔄 Latest code pulled from main branch
- [ ] 🗑️ Old deployments cleaned up (if switching methods)

---

## 🧹 Cleanup Commands

### Stop Docker Compose
```bash
docker-compose down

# With volume cleanup
docker-compose down -v
```

### Stop K3d
```bash
# Delete cluster
k3d cluster delete budget-cluster

# Stop port-forward (if running)
pkill -f 'kubectl.*port-forward'
```

### Full Cleanup (Both)
```bash
# Stop everything
docker-compose down -v
k3d cluster delete budget-cluster
pkill -f 'kubectl.*port-forward'

# Clean Docker images (optional)
docker system prune -a
```

---

## 🔍 Verification After Deployment

### Docker Compose
```bash
# Check services
docker-compose ps

# Should show:
# web        Up      8887->5000
# postgres   Up      5432
# nginx      Up      8887->80

# Check logs
docker-compose logs -f web

# Test endpoint
curl http://localhost:8887/api/health
```

### K3d
```bash
# Check pods
kubectl get pods -n budget-app

# Should show all Running:
# flask-app-xxx    2/2   Running
# nginx-xxx        1/1   Running
# postgres-xxx     1/1   Running
# prometheus-xxx   1/1   Running
# grafana-xxx      1/1   Running

# Check services
kubectl get services -n budget-app

# Test endpoint
curl http://localhost:8889/api/health
```

---

## 🚨 Troubleshooting Deployment

### Docker Compose Issues

**Port already in use:**
```bash
# Kill process on port 8887
lsof -ti:8887 | xargs kill -9

# Or use different port
docker-compose down
# Edit docker-compose.yml ports
docker-compose up -d
```

**Database connection error:**
```bash
# Check postgres is running
docker-compose ps postgres

# Restart database
docker-compose restart postgres

# Check logs
docker-compose logs postgres
```

### K3d Issues

**Pods stuck in Pending:**
```bash
# Check events
kubectl get events -n budget-app --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n budget-app

# Common cause: Image not imported
k3d image import devops-final-project-web:latest -c budget-cluster
```

**Can't access via LoadBalancer:**
```bash
# Check service
kubectl get svc nginx-service -n budget-app

# Use port-forward as fallback
kubectl port-forward svc/nginx-service 8889:80 -n budget-app
```

**Cluster won't start:**
```bash
# Delete and recreate
k3d cluster delete budget-cluster
k3d cluster create budget-cluster --port "8889:80@loadbalancer"
```

---

## 📊 Monitoring Deployment

### Docker Compose Monitoring
```bash
# Access Prometheus
open http://localhost:9090

# Access Grafana
open http://localhost:3000
# Login: admin / admin
```

### K3d Monitoring
```bash
# Port-forward Prometheus
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090

# Port-forward Grafana
kubectl port-forward -n budget-app svc/grafana-service 3000:3000

# Access
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

---

## 🎓 Best Practices

### Development Cycle
```bash
1. Make code changes
2. Test locally with Docker Compose
3. Commit and push (triggers CI)
4. Wait for CI to pass ✅
5. Test with K3d before demo/presentation
```

### Branch Strategy
```bash
main branch:
  ├─ Always keep stable
  ├─ CI must pass before merge
  └─ Deploy from here for presentations

feature branches:
  ├─ For development
  ├─ Test with Docker Compose
  └─ Create PR to main
```

### Before Presentation
```bash
# 1 day before
1. Merge all features to main
2. Verify CI passes
3. Test full deployment on K3d
4. Verify monitoring works

# 1 hour before
1. Fresh K3d deployment
2. Test all features
3. Prepare demo data
4. Keep cluster running
```

---

## 🚀 Future: Automated CD

If you want to add automated CD in the future, options include:

### Option 1: Self-Hosted Runner
```yaml
# .github/workflows/cd.yml
name: CD to Local K3d

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: self-hosted  # Your laptop
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to K3d
        run: |
          k3d cluster delete budget-cluster || true
          k3d cluster create budget-cluster --port "8889:80@loadbalancer"
          kubectl apply -f k8s/
```

**Requires:** GitHub Actions self-hosted runner installed on your machine

### Option 2: Remote Kubernetes Cluster
```yaml
# Deploy to remote cluster (requires cloud provider)
- name: Deploy to Remote K8s
  run: |
    kubectl config use-context remote-cluster
    kubectl apply -f k8s/
```

**Requires:** Remote Kubernetes cluster (GKE, EKS, AKS, etc.)

### Option 3: ArgoCD (GitOps)
```bash
# Install ArgoCD on K3d
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# ArgoCD watches Git repo and auto-deploys
```

**Complexity:** High, but industry best practice

---

## 📚 Related Documentation

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Step-by-step deployment guide
- [KUBERNETES_ARCHITECTURE.md](KUBERNETES_ARCHITECTURE.md) - K8s components
- [MONITORING.md](MONITORING.md) - Monitoring setup
- [CI/CD Workflow](.github/workflows/ci.yml) - CI configuration

---

## ❓ FAQ

**Q: Why no automated CD?**  
A: Both deployment targets (Docker Compose and K3d) run locally. CD typically deploys to remote servers.

**Q: Should I use Docker Compose or K3d?**  
A: Both! Docker Compose for quick dev, K3d for K8s testing and demos.

**Q: Can I run both simultaneously?**  
A: Yes! They use different ports (8887 and 8889).

**Q: How do I know if CI passed?**  
A: Check the green checkmark next to your commit on GitHub.

**Q: What if I want real automated CD?**  
A: You'd need a remote environment (cloud VM, Kubernetes cluster, etc.).

---

**Remember: CI is automated ✅ | CD is manual for local environments 📋**

