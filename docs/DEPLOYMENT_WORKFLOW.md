# 🚀 Deployment Workflow

## Overview

This project uses **GitOps CI/CD** with GitHub Actions and ArgoCD for automated deployment.

```
┌─────────────────────────────────────────────────────────────┐
│                  GitOps Workflow                             │
└─────────────────────────────────────────────────────────────┘

1. Code Changes (Local)
   ↓
2. Git Push to GitHub
   ↓
3. CI Pipeline (Automated)
   ├── Build multi-platform Docker images
   ├── Run tests & linting
   ├── Security scan (Trivy)
   ├── Push to GHCR with SHA tag
   └── Update K8s manifest with new image
   ↓
4. CD Pipeline (Automated - ArgoCD)
   ├── Detects manifest change
   ├── Pulls new image
   └── Deploys automatically
   ↓
5. ✅ New version running!
```

---

## 🔄 Continuous Integration (CI)

**Automated on every push to main branch**

### What Happens:
1. **Checkout code** from GitHub
2. **Build multi-platform Docker images** (linux/amd64, linux/arm64)
3. **Run linting** with Flake8 (code quality checks)
4. **Security scan** with Trivy (filesystem and container image)
5. **Push to GHCR** with immutable SHA tags
6. **Update Kubernetes manifest** with new image tag
7. **Commit manifest back to Git** (triggers GitOps)

### Status:
- ✅ **Workflow file:** `.github/workflows/ci-cd-gitops.yml`
- ✅ **Triggered on:** Push to main branch, Pull requests
- ✅ **Registry:** GitHub Container Registry (GHCR)
- ✅ **Tags:** `sha-XXXXXXX` (immutable), `latest`, `main`

### View CI Status:
```bash
# Check latest CI run
https://github.com/ChenBracha/devops-final-project/actions
```

---

## 📦 Continuous Deployment (CD)

**Fully automated with ArgoCD (GitOps)**

This project uses **ArgoCD** for automated continuous deployment:

> **How it works:**
> 1. CI updates Kubernetes manifest in Git with new image tag
> 2. ArgoCD polls Git every 3 minutes
> 3. ArgoCD detects the change
> 4. ArgoCD automatically syncs to the cluster
> 5. New version deployed! 🚀

**Benefits:**
- ✅ Pull-based deployment (more secure)
- ✅ Git as single source of truth
- ✅ Self-healing (auto-reverts manual changes)
- ✅ Easy rollback (just revert Git commit)
- ✅ Full audit trail in Git history

Here's the workflow:

### Step 1: Initial Setup (One-Time)
```bash
# Run the deployment script
python3 deploy.py

# This will:
# 1. Create K3d cluster
# 2. Install ArgoCD
# 3. Deploy application
# 4. Set up GitOps

# Access:
# - Budget App: http://localhost:8080
# - ArgoCD UI: https://localhost:8443
```

### Step 2: Make Code Changes
```bash
# 1. Make your changes
vim app/main.py

# 2. Commit and push
git add app/main.py
git commit -m "feat: Add new feature"
git push origin main
```

### Step 3: Watch CI/CD Happen Automatically
```bash
# 1. GitHub Actions builds image and updates manifest
# Visit: https://github.com/ChenBracha/devops-final-project/actions

# 2. ArgoCD detects change and deploys automatically (within 3 min)
# Visit: https://localhost:8443

# 3. Check deployment
kubectl get pods -n budget-app -w
```

**That's it!** Fully automated deployment via GitOps.

---

## 🎯 GitOps Workflow Diagram

```
┌──────────────────────────────────────────────────────┐
│              Complete GitOps Flow                     │
└──────────────────────────────────────────────────────┘

Developer → Git Push
     ↓
GitHub Actions (CI)
  ├─ Build multi-platform image
  ├─ Tag: sha-XXXXXXX
  ├─ Push to GHCR
  ├─ Update k8s/flask-app/deployment.yml
  └─ Commit back to Git [skip ci]
     ↓
ArgoCD (CD) - Polls every 3 min
  ├─ Detect manifest change
  ├─ Pull new image from GHCR
  ├─ Rolling update (2 replicas)
  └─ Health check
     ↓
✅ New version deployed!
```

---

## 📋 Pre-Deployment Checklist

Before initial deployment, verify:

- [ ] 🐳 Docker Desktop is running
- [ ] ✅ kubectl installed
- [ ] ✅ k3d installed
- [ ] 📝 Secrets configured in `k8s/*/secret.yml`
- [ ] 🔐 GitHub repository access (for ArgoCD)

---

## 🧹 Cleanup Commands

### Delete K3d Cluster
```bash
# Delete entire cluster
k3d cluster delete budget-cluster

# Stop port-forward (if any)
pkill -f 'kubectl.*port-forward'
```

### Clean Docker Resources
```bash
# Remove unused images
docker system prune -a

# Remove specific image versions
docker rmi ghcr.io/chenbracha/devops-final-project:sha-XXXXXXX
```

---

## 🔍 Verification After Deployment

### Check K3d Cluster
```bash
# Check cluster
k3d cluster list

# Check ArgoCD
kubectl get pods -n argocd

# Check application
kubectl get application -n argocd

# Check app pods
kubectl get pods -n budget-app

# Should show all Running:
# flask-app-xxx    1/1   Running
# nginx-xxx        1/1   Running
# postgres-xxx     1/1   Running
# prometheus-xxx   1/1   Running
# grafana-xxx      1/1   Running

# Test endpoints
curl http://localhost:8080/api/health
curl -k https://localhost:8443  # ArgoCD UI
```

---

## 🚨 Troubleshooting Deployment

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

# Check ingress
kubectl get ingress -A

# Use port-forward as fallback
kubectl port-forward svc/nginx-service 8080:80 -n budget-app
```

**Cluster won't start:**
```bash
# Delete and recreate
k3d cluster delete budget-cluster
k3d cluster create budget-cluster \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer"
```

---

## 📊 Monitoring Deployment

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
1. Make code changes locally
2. Commit and push (triggers CI/CD)
3. GitHub Actions builds & updates manifest
4. ArgoCD auto-deploys within 3 minutes
5. Verify deployment in ArgoCD UI
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
2. Verify CI/CD pipeline passes
3. Check ArgoCD shows "Synced" and "Healthy"
4. Test all application features
5. Verify monitoring works

# 1 hour before
1. Restart cluster if needed: python3 deploy.py
2. Test Budget App: http://localhost:8080
3. Check ArgoCD UI: https://localhost:8443
4. Verify all pods are Running
5. Prepare demo flow
```

---

## 🚀 Production Deployment Options

### Current Setup (Local K3d)
✅ **Already implemented!** You have:
- GitOps with ArgoCD
- Automated CI/CD pipeline
- Multi-platform Docker images
- Security scanning

### Option 1: Cloud Kubernetes
```bash
# Deploy to GKE (Google Kubernetes Engine)
gcloud container clusters create budget-cluster \
  --num-nodes=3 --zone=us-central1-a

# Or deploy to EKS (AWS)
eksctl create cluster --name budget-cluster --region us-east-1

# Or deploy to AKS (Azure)
az aks create --resource-group myRG --name budget-cluster
```

**Then:**
- Point ArgoCD to your cloud cluster
- Same GitOps workflow continues to work!

### Option 2: Cloud Run / App Engine
```bash
# Deploy as serverless
gcloud run deploy budget-app \
  --image ghcr.io/chenbracha/devops-final-project:latest \
  --platform managed
```

### Option 3: Hybrid (Dev + Prod)
- **Dev:** K3d (local) ← You're here
- **Staging:** Cloud K8s cluster
- **Prod:** Cloud K8s cluster with HA

ArgoCD can manage all environments from Git!

---

## 📚 Related Documentation

- [DEPLOYMENT.md](../DEPLOYMENT.md) - Step-by-step deployment guide
- [KUBERNETES_ARCHITECTURE.md](KUBERNETES_ARCHITECTURE.md) - K8s components
- [MONITORING.md](MONITORING.md) - Monitoring setup
- [CI/CD Workflow](.github/workflows/ci.yml) - CI configuration

---

## ❓ FAQ

**Q: Is CD automated?**  
A: Yes! ArgoCD automatically deploys changes from Git within 3 minutes.

**Q: How do I trigger a deployment?**  
A: Just push to main branch. CI builds the image, updates the manifest, and ArgoCD deploys automatically.

**Q: Can I deploy to cloud?**  
A: Yes! Point ArgoCD to a cloud K8s cluster. The same workflow works.

**Q: How do I know if CI passed?**  
A: Check the green checkmark next to your commit on GitHub.

**Q: How do I rollback?**  
A: Use ArgoCD UI or: `git revert <commit-hash> && git push`

---

**Remember: Both CI and CD are fully automated! 🚀**

