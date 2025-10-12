# 🚀 Deployment Guide - K3d + ArgoCD GitOps

This project uses **Kubernetes (K3d) with ArgoCD** for a production-grade GitOps deployment.

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                   Your Laptop                            │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │           K3d Cluster (K3s in Docker)          │    │
│  │                                                 │    │
│  │  ┌─────────────────────────────────────────┐  │    │
│  │  │  ArgoCD Namespace                       │  │    │
│  │  │  (GitOps Controller - runs as pods)     │  │    │
│  │  │                                          │  │    │
│  │  │  • argocd-server (UI)                   │  │    │
│  │  │  • argocd-repo-server (Git sync)        │  │    │
│  │  │  • argocd-application-controller        │  │    │
│  │  │  • argocd-redis                         │  │    │
│  │  └─────────────────────────────────────────┘  │    │
│  │                                                 │    │
│  │  ┌─────────────────────────────────────────┐  │    │
│  │  │  Budget-App Namespace                   │  │    │
│  │  │  (Your Application)                     │  │    │
│  │  │                                          │  │    │
│  │  │  • flask-app pods                       │  │    │
│  │  │  • nginx pods                           │  │    │
│  │  │  • postgres pods                        │  │    │
│  │  │  • prometheus pods                      │  │    │
│  │  │  • grafana pods                         │  │    │
│  │  └─────────────────────────────────────────┘  │    │
│  └────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

**Key Points:**
- ✅ K3d creates a lightweight K3s cluster inside Docker
- ✅ ArgoCD runs as pods INSIDE the cluster
- ✅ Your application is managed by ArgoCD via GitOps
- ✅ Everything runs on your laptop (no cloud needed)

---

## 📋 Prerequisites

### Required Tools

<details>
<summary>📦 macOS</summary>

```bash
# Install via Homebrew
brew install docker kubectl k3d

# Verify
docker --version
kubectl version --client
k3d version
```
</details>

<details>
<summary>🐧 Linux (Ubuntu/Debian)</summary>

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install k3d
curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash

# Logout and login for docker group to take effect
```
</details>

<details>
<summary>🪟 Windows</summary>

```powershell
# Install via Chocolatey
choco install docker-desktop kubectl k3d

# Or via Scoop
scoop install kubectl k3d

# Or download Docker Desktop
# https://www.docker.com/products/docker-desktop
```
</details>

---

## 🚀 Quick Start (One Command)

```bash
python3 deploy.py
```

**That's it!** The script will:
1. ✅ Check prerequisites
2. ✅ Create K3d cluster
3. ✅ Install ArgoCD (as pods)
4. ✅ Deploy your application
5. ✅ Show access information

---

## 📖 Step-by-Step Deployment

If you want to understand what `deploy.py` does:

### Step 1: Create K3d Cluster

```bash
# Create cluster with port mapping
k3d cluster create budget-cluster --port "8889:80@loadbalancer"

# Verify cluster is running
kubectl cluster-info
kubectl get nodes
```

**What happens:**
- K3d creates a K3s (lightweight Kubernetes) cluster
- Runs inside Docker containers
- Port 8889 on your laptop maps to port 80 in the cluster

### Step 2: Install ArgoCD

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for pods to be ready (2-3 minutes)
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

# Check ArgoCD pods
kubectl get pods -n argocd
```

**What happens:**
- ArgoCD installs multiple pods in the `argocd` namespace
- These pods constantly watch your Git repository
- When you push changes to Git, ArgoCD auto-deploys them

### Step 3: Deploy Application

```bash
# Apply ArgoCD application definition
kubectl apply -f argocd/application.yaml

# Check application status
kubectl get application -n argocd

# Wait for sync
kubectl get application budget-app -n argocd -w
```

**What happens:**
- ArgoCD reads `argocd/application.yaml`
- It knows to deploy from `k8s/` directory
- Automatically creates all your pods, services, etc.

### Step 4: Access Services

```bash
# Get ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d

# Access ArgoCD UI (in another terminal)
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open: https://localhost:8080
# Login: admin / <password-from-above>

# Application is already accessible at:
# http://localhost:8889
```

---

## 🔍 Understanding the Architecture

### Namespace Separation

```
argocd (namespace)
├── ArgoCD controller pods
└── Manages all deployments

budget-app (namespace)
├── flask-app (your application)
├── nginx (reverse proxy)
├── postgres (database)
├── prometheus (metrics)
└── grafana (dashboards)
```

### Port Mapping

| Service | Internal Port | External Access |
|---------|--------------|-----------------|
| Flask App | 5000 | Via Nginx |
| Nginx | 80 | http://localhost:8889 |
| PostgreSQL | 5432 | Internal only |
| ArgoCD UI | 443 | https://localhost:8080 (port-forward) |
| Prometheus | 9090 | kubectl port-forward |
| Grafana | 3000 | kubectl port-forward |

### Data Persistence

```bash
# Persistent volumes for:
- PostgreSQL data (survives pod restarts)
- Prometheus metrics
- Grafana dashboards

# View persistent volumes
kubectl get pv
kubectl get pvc -n budget-app
```

---

## 🔄 GitOps Workflow

### How It Works

```
1. Developer pushes code to Git
   ↓
2. GitHub Actions (CI)
   ├─ Run tests
   ├─ Build Docker image
   ├─ Scan with Trivy
   └─ Push to GHCR (GitHub Container Registry)
   ↓
3. Update k8s manifest with new image tag
   ↓
4. ArgoCD (running in cluster)
   ├─ Polls Git every 3 minutes
   ├─ Detects new image tag
   ├─ Pulls image from GHCR
   └─ Deploys automatically
   ↓
5. ✅ New version running!
```

### Making Changes

**Option 1: Code Change**
```bash
# 1. Change code
echo "# New feature" >> app/main.py

# 2. Push to Git
git add app/main.py
git commit -m "feat: New feature"
git push

# 3. GitHub Actions builds image
# 4. Update manifest with new tag
vim k8s/flask-app/deployment.yml
# Change image tag to new commit SHA

git add k8s/flask-app/deployment.yml
git commit -m "chore: Update image"
git push

# 5. ArgoCD auto-deploys (wait 3 min or click Sync in UI)
```

**Option 2: Add New Service**
```bash
# 1. Create new K8s manifest
mkdir k8s/redis
cat > k8s/redis/deployment.yml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: budget-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:alpine
        ports:
        - containerPort: 6379
EOF

# 2. Push to Git
git add k8s/redis/
git commit -m "feat: Add Redis"
git push

# 3. ArgoCD detects new manifest and deploys Redis
#    (within 3 minutes)
```

---

## 🎨 ArgoCD UI

### Access the UI

```bash
# Port forward (keep this terminal open)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Open browser
open https://localhost:8080

# Login
# Username: admin
# Password: <from secret>
```

### What You'll See

1. **Applications Dashboard**
   - "budget-app" application
   - Sync status (Synced/OutOfSync)
   - Health status (Healthy/Degraded)

2. **Application Details** (click on budget-app)
   - Visual graph of all resources
   - Deployments → ReplicaSets → Pods
   - Services, ConfigMaps, Secrets
   - Real-time status

3. **Useful Actions**
   - **Sync** - Manual sync (don't wait 3 min)
   - **Refresh** - Check Git for changes
   - **Rollback** - Revert to previous version
   - **Diff** - Show Git vs cluster differences

---

## 🛠️ Management Commands

### View Everything

```bash
# All ArgoCD applications
kubectl get application -n argocd

# ArgoCD pods
kubectl get pods -n argocd

# Your application pods
kubectl get pods -n budget-app

# All resources in budget-app
kubectl get all -n budget-app

# Persistent volumes
kubectl get pv,pvc -n budget-app
```

### Logs

```bash
# Flask app logs
kubectl logs -f deployment/flask-app -n budget-app

# Nginx logs
kubectl logs -f deployment/nginx -n budget-app

# PostgreSQL logs
kubectl logs -f deployment/postgres -n budget-app

# ArgoCD controller logs
kubectl logs -f -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### Troubleshooting

```bash
# Check pod status
kubectl describe pod <pod-name> -n budget-app

# Check events
kubectl get events -n budget-app --sort-by='.lastTimestamp'

# Force ArgoCD sync
kubectl patch application budget-app -n argocd --type merge \
  -p '{"operation":{"sync":{}}}'

# Restart deployment
kubectl rollout restart deployment/flask-app -n budget-app

# Check ArgoCD application status
kubectl get application budget-app -n argocd -o yaml
```

### Cleanup

```bash
# Delete everything
k3d cluster delete budget-cluster

# Or just delete app (keep cluster and ArgoCD)
kubectl delete application budget-app -n argocd
kubectl delete namespace budget-app
```

---

## 🔐 Security

### Secrets Management

```bash
# Secrets are stored as Kubernetes Secrets
kubectl get secrets -n budget-app

# View secret (base64 encoded)
kubectl get secret postgres-secret -n budget-app -o yaml

# For production, use:
# - Sealed Secrets
# - External Secrets Operator
# - HashiCorp Vault
```

### Image Registry

```bash
# Images from GHCR (GitHub Container Registry)
# Public: No authentication needed
# Private: Create imagePullSecret

kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PAT \
  -n budget-app
```

---

## 📊 Monitoring

### Prometheus

```bash
# Access Prometheus
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090

# Open: http://localhost:9090
```

### Grafana

```bash
# Access Grafana
kubectl port-forward -n budget-app svc/grafana-service 3000:3000

# Open: http://localhost:3000
# Login: admin / admin
```

See [MONITORING.md](docs/MONITORING.md) for detailed monitoring setup.

---

## ❓ FAQ

### Why K3d?

- ✅ Lightweight K3s in Docker
- ✅ Fast startup (30 seconds)
- ✅ Runs on laptop
- ✅ Production-like Kubernetes
- ✅ No cloud costs

### Why ArgoCD?

- ✅ GitOps best practice
- ✅ Pull-based (more secure)
- ✅ Self-healing
- ✅ Easy rollbacks
- ✅ Rich UI
- ✅ Industry standard

### Can I use Minikube instead?

Yes! Just change:
```bash
# Instead of:
k3d cluster create budget-cluster --port "8889:80@loadbalancer"

# Use:
minikube start
kubectl port-forward -n budget-app svc/nginx-service 8889:80
```

### How to update Python code?

1. Push code to Git
2. CI builds new image
3. Update `k8s/flask-app/deployment.yml` with new image tag
4. Push manifest change
5. ArgoCD auto-deploys

### How to scale?

```bash
# Edit replicas in manifest
vim k8s/flask-app/deployment.yml
# Change replicas: 1 → replicas: 3

# Push to Git
git add k8s/flask-app/deployment.yml
git commit -m "scale: Increase replicas to 3"
git push

# ArgoCD auto-scales
```

---

## 📚 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [K3d Documentation](https://k3d.io/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [GitOps Principles](https://opengitops.dev/)

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] K3d cluster running: `k3d cluster list`
- [ ] ArgoCD pods running: `kubectl get pods -n argocd`
- [ ] Application synced: `kubectl get application -n argocd`
- [ ] App pods running: `kubectl get pods -n budget-app`
- [ ] App accessible: http://localhost:8889
- [ ] ArgoCD UI accessible: https://localhost:8080 (after port-forward)
- [ ] Can login to ArgoCD
- [ ] Can see application in ArgoCD UI
- [ ] Monitoring works: Prometheus & Grafana

---

**🎉 Congratulations! You have a production-grade GitOps deployment!**
