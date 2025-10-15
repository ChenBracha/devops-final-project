# 🔄 GitOps with ArgoCD - Complete Guide

## 🎯 What is GitOps?

**GitOps** = Git is the single source of truth for your infrastructure and applications.

```
Git Repository → ArgoCD → Kubernetes Cluster
   (Source)      (Sync)      (Desired State)
```

**Core Principle:** The cluster **pulls** updates from Git, instead of CI **pushing** to it.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     Complete GitOps Flow                          │
└──────────────────────────────────────────────────────────────────┘

1️⃣ Developer → Git Push (new code)
   ↓
2️⃣ GitHub Actions (CI):
   ├─ Build Docker image
   ├─ Tag with commit SHA (abc123)
   ├─ Scan with Trivy
   └─ Push to GHCR (ghcr.io/username/app:abc123)
   ↓
3️⃣ Update K8s manifest with new tag
   ├─ Edit k8s/flask-app/deployment.yml
   └─ Git push
   ↓
4️⃣ ArgoCD (CD):
   ├─ Polls Git repo every 3 minutes
   ├─ Detects new image tag in manifests
   ├─ Compares with cluster state
   ├─ Syncs automatically
   └─ Deploys new version
   ↓
5️⃣ Kubernetes:
   ├─ Pulls image from GHCR
   ├─ Rolling update
   └─ ✅ Deployment complete!
```

---

## 📋 Prerequisites

- ✅ K3d cluster running
- ✅ kubectl installed
- ✅ GitHub account
- ✅ Git installed
- ✅ ~20 minutes

---

## 🚀 Part 1: Install ArgoCD on K3d

### Step 1: Verify Cluster is Running

```bash
# Check if cluster exists
k3d cluster list

# If not exists, create it
k3d cluster create budget-cluster \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer"

# Verify connection
kubectl cluster-info
kubectl get nodes
```

### Step 2: Create Namespace for ArgoCD

```bash
kubectl create namespace argocd
```

### Step 3: Install ArgoCD

```bash
# Download and install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for all pods to be ready (takes 2-3 minutes)
echo "⏳ Waiting for ArgoCD to be ready..."
kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s

echo "✅ ArgoCD installed successfully!"
```

### Step 4: Access ArgoCD UI

```bash
# Get the initial admin password
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d)

echo "📊 ArgoCD Login Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "URL:      https://localhost:8443"
echo "Username: admin"
echo "Password: $ARGOCD_PASSWORD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 Ignore the SSL warning (self-signed certificate)"
echo "💡 ArgoCD is accessible directly (no port-forward needed!)"

# Open browser (macOS)
open https://localhost:8443
```

**Note:** 
- ArgoCD UI is accessible directly via Traefik ingress at `https://localhost:8443`
- You'll see an SSL warning - click "Advanced" → "Proceed" (it's safe, self-signed certificate)
- No port-forwarding needed!

---

## 📦 Part 2: Configure Project for GitOps

### Step 1: Update K8s Manifests to Use GHCR

We need to change the image from local to GHCR registry:

```bash
# Edit flask-app deployment
vim k8s/flask-app/deployment.yml
```

**Find and change these lines:**

```yaml
# BEFORE (lines 20-21):
image: devops-final-project-web:latest
imagePullPolicy: Never

# AFTER:
image: ghcr.io/chenbracha/devops-final-project:latest
imagePullPolicy: Always
```

**Save and close the file.**

### Step 2: Create ArgoCD Application Definition

Create the ArgoCD configuration:

```bash
# Create argocd directory
mkdir -p argocd

# Create application definition
cat > argocd/application.yaml << 'EOF'
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: budget-app
  namespace: argocd
spec:
  project: default
  
  # Source: Where to get the manifests
  source:
    repoURL: https://github.com/ChenBracha/devops-final-project.git
    targetRevision: main
    path: k8s
  
  # Destination: Where to deploy
  destination:
    server: https://kubernetes.default.svc
    namespace: budget-app
  
  # Sync Policy: How to deploy
  syncPolicy:
    automated:
      prune: true        # Delete resources removed from Git
      selfHeal: true     # Auto-fix manual changes
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

echo "✅ ArgoCD application definition created!"
```

### Step 3: Apply ArgoCD Application

```bash
# Apply the configuration
kubectl apply -f argocd/application.yaml

# Check status
kubectl get application -n argocd

# Watch it sync (Ctrl+C to exit)
kubectl get application budget-app -n argocd -w
```

You should see:
```
NAME         SYNC STATUS   HEALTH STATUS
budget-app   Synced        Healthy
```

---

## 🎯 Part 3: Complete Workflow Test

### Test 1: Code Change with Manual Image Update

Let's test the complete GitOps flow:

#### 3.1: Make a Code Change

```bash
# Make a simple change
echo "# GitOps test" >> app/main.py
```

#### 3.2: Commit and Push

```bash
git add app/main.py
git commit -m "test: GitOps workflow"
git push origin main
```

#### 3.3: Watch GitHub Actions Build

```bash
# Go to your repo
open https://github.com/ChenBracha/devops-final-project/actions

# You should see:
# - CI running
# - Building image
# - Pushing to GHCR with tag (commit SHA)
```

#### 3.4: Update Manifest with New Image Tag

After CI completes, get the new image tag:

```bash
# Get the commit SHA
git log -1 --format=%H

# Example output: abc123def456...
```

Update the manifest:

```bash
# Edit deployment
vim k8s/flask-app/deployment.yml

# Change line 20 to use new tag:
# image: ghcr.io/chenbracha/devops-final-project:abc123d
# (use first 7 chars of commit SHA)

# Save and push
git add k8s/flask-app/deployment.yml
git commit -m "chore: Update image to new version"
git push
```

#### 3.5: Watch ArgoCD Deploy Automatically

```bash
# Watch ArgoCD detect and sync (takes up to 3 minutes)
kubectl get application budget-app -n argocd -w

# Watch pods update
kubectl get pods -n budget-app -w

# You'll see:
# - Old pods terminating
# - New pods starting
# - Rolling update in progress
```

**Or check in ArgoCD UI:**
- Go to https://localhost:8443
- Click on "budget-app"
- Watch the sync happen visually!

---

### Test 2: Add New Service (nginx2)

Test that ArgoCD detects new Kubernetes resources:

```bash
# Create new service
mkdir -p k8s/nginx2

cat > k8s/nginx2/deployment.yml << 'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx2
  namespace: budget-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx2
  template:
    metadata:
      labels:
        app: nginx2
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx2-service
  namespace: budget-app
spec:
  selector:
    app: nginx2
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
EOF

# Commit and push
git add k8s/nginx2/
git commit -m "feat: Add nginx2 service for testing"
git push

# Watch ArgoCD deploy it automatically (within 3 minutes)
kubectl get pods -n budget-app -w

# You should see nginx2 pod appear!
```

---

## 🎨 Part 4: ArgoCD UI Overview

### Access UI

```bash
# ArgoCD UI is directly accessible (no port-forward needed!)
open https://localhost:8443
```

### What You'll See:

1. **Applications Dashboard**
   - List of all applications
   - "budget-app" with sync/health status

2. **Click on "budget-app"**
   - Visual graph of all resources
   - Deployment → ReplicaSet → Pods
   - Services, ConfigMaps, Secrets, etc.

3. **Sync Status**
   - 🟢 Synced = Git matches cluster
   - 🟡 Out of Sync = Git differs from cluster
   - Last sync time

4. **Health Status**
   - 🟢 Healthy = All resources running
   - 🔴 Degraded = Some issues

5. **History Tab**
   - All past deployments
   - Rollback to any version

### Useful Actions:

- **Sync Now** - Manual sync (don't wait 3 min)
- **Refresh** - Check Git for changes
- **Rollback** - Revert to previous version
- **Diff** - Show differences between Git and cluster

---

## 🔍 Part 5: Troubleshooting

### Issue: ArgoCD Not Syncing

```bash
# Check application status
kubectl get application budget-app -n argocd -o yaml

# Check ArgoCD logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller

# Manual sync
kubectl patch application budget-app -n argocd --type merge \
  -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

### Issue: Can't Pull Image from GHCR

The image on GHCR might be private. Two solutions:

**Option 1: Make Package Public**
```bash
# Go to: https://github.com/users/ChenBracha/packages
# Click on your package
# Package settings → Change visibility → Public
```

**Option 2: Create Image Pull Secret**
```bash
# Create GitHub Personal Access Token (PAT)
# Go to: https://github.com/settings/tokens
# Generate new token (classic)
# Select: read:packages

# Create secret in K8s
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_PAT \
  -n budget-app

# Update k8s/flask-app/deployment.yml:
# Add under spec.template.spec:
#   imagePullSecrets:
#   - name: ghcr-secret
```

### Issue: Pods Stuck

```bash
# Check events
kubectl get events -n budget-app --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -f deployment/flask-app -n budget-app

# Describe pod
kubectl describe pod <pod-name> -n budget-app
```

---

## 📊 Part 6: Monitoring

### Watch in Real-Time

```bash
# Watch applications
watch kubectl get application -n argocd

# Watch pods
watch kubectl get pods -n budget-app

# Watch events
kubectl get events -n budget-app -w --sort-by='.lastTimestamp'
```

### ArgoCD CLI (Optional)

```bash
# Install ArgoCD CLI
brew install argocd

# Login
argocd login localhost:8080

# List apps
argocd app list

# Get app details
argocd app get budget-app

# Sync manually
argocd app sync budget-app

# Watch sync
argocd app wait budget-app
```

---

## 🎓 Part 7: For Your DevSecOps Presentation

### What to Show:

#### 1. Show the Architecture

```
"I implemented GitOps using ArgoCD. Here's how it works:

1. Developer pushes code to Git
2. CI builds and pushes image to GHCR
3. Manifest is updated with new image tag
4. ArgoCD detects change in Git
5. Automatically deploys to cluster

This is a pull-based approach - the cluster pulls from Git,
rather than CI pushing to the cluster."
```

#### 2. Live Demo

```bash
# Show ArgoCD UI
open https://localhost:8443

# Make a change
echo "# Demo" >> app/main.py
git add app/main.py
git commit -m "demo: GitOps in action"
git push

# Show in ArgoCD UI how it syncs automatically
```

#### 3. Explain Benefits

> **Security:**
> - Cluster credentials never leave the cluster
> - No need to expose cluster to CI
> - Git is the single source of truth
> 
> **Version Control:**
> - Every change tracked in Git
> - Easy rollback (git revert)
> - Full audit trail
> 
> **Automation:**
> - Self-healing: If someone makes manual changes, ArgoCD reverts them
> - Drift detection: Constantly compares Git vs cluster
> - Automated sync: Updates happen automatically
> 
> **Industry Standard:**
> - GitOps is the modern best practice
> - ArgoCD is the most popular tool
> - Used by Netflix, Adobe, Intuit, etc.

---

## 🎯 Part 8: GitOps vs Traditional CD

| Aspect | Traditional CD | GitOps with ArgoCD |
|--------|---------------|-------------------|
| **Security** | CI needs cluster credentials | No credentials in CI |
| **Visibility** | Logs in CI | Rich UI with graph |
| **Rollback** | Manual/complex | One click |
| **Drift Detection** | ❌ No | ✅ Yes |
| **Self-Healing** | ❌ No | ✅ Yes |
| **Multi-cluster** | Difficult | Easy |
| **Audit** | CI logs | Git history + ArgoCD |

---

## 🔐 Part 9: GitHub Secrets Setup

You'll need to configure these secrets for CI to push to GHCR:

```bash
# Go to your GitHub repo
# Settings → Secrets and variables → Actions
# Note: GITHUB_TOKEN is already available, no need to create

# If you want to use a Personal Access Token instead:
# 1. GitHub → Settings → Developer settings → Personal access tokens
# 2. Generate new token (classic)
# 3. Select scopes: write:packages, read:packages
# 4. Copy token
# 5. Add as secret named GHCR_TOKEN (if you want to use it)

# Our workflow uses GITHUB_TOKEN by default (easier)
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] K3d cluster running: `k3d cluster list`
- [ ] ArgoCD installed: `kubectl get pods -n argocd`
- [ ] ArgoCD UI accessible: https://localhost:8443
- [ ] Application created: `kubectl get application -n argocd`
- [ ] Application synced: Status shows "Synced" and "Healthy"
- [ ] Pods running: `kubectl get pods -n budget-app`
- [ ] CI pushes to GHCR: Check GitHub Actions
- [ ] Can make changes and see them deploy
- [ ] New services auto-deploy

---

## 🚀 Quick Reference Commands

```bash
# ArgoCD UI (direct access via ingress)
open https://localhost:8443

# Get password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Check application
kubectl get application -n argocd
kubectl get application budget-app -n argocd -o yaml

# Manual sync
kubectl patch application budget-app -n argocd --type merge \
  -p '{"operation":{"sync":{}}}'

# Watch deployment
kubectl get pods -n budget-app -w

# Check image being used
kubectl get deployment flask-app -n budget-app -o jsonpath='{.spec.template.spec.containers[0].image}'
```

---

## 📚 Additional Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

---

## 🎉 Summary

**You now have:**
- ✅ CI: Automated build, test, scan, push to GHCR
- ✅ CD: GitOps with ArgoCD (pull-based)
- ✅ Industry standard workflow
- ✅ Production-ready setup
- ✅ Ready for presentation!

**Your workflow:**
```
Code → Git Push → CI builds image → Push to GHCR → 
Update manifest → ArgoCD syncs → Deployed! 🚀
```

---

**Congratulations! You have a professional GitOps CI/CD pipeline!** 🎉
