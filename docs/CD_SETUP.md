# 🚀 Continuous Deployment Setup Guide

## Overview

This project uses **GitHub Actions with a self-hosted runner** for continuous deployment to your local K3d cluster.

**How it works:**
```
Git Push → GitHub Actions → Your Laptop → K3d Cluster
```

**Advantages:**
- ✅ Real CD (automated deployment)
- ✅ No Docker Hub/registry needed
- ✅ Uses local images
- ✅ Detects new services automatically
- ✅ Works with existing setup

---

## 🔧 Setup (One-Time, ~15 minutes)

### Step 1: Install GitHub Actions Self-Hosted Runner

1. **Go to your GitHub repository:**
   ```
   https://github.com/YOUR_USERNAME/devops-final-project/settings/actions/runners/new
   ```

2. **Select macOS and follow the commands shown:**
   
   Example (your commands will be different):
   ```bash
   # Create a folder
   mkdir actions-runner && cd actions-runner
   
   # Download the latest runner package
   curl -o actions-runner-osx-x64-2.311.0.tar.gz -L \
     https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-osx-x64-2.311.0.tar.gz
   
   # Extract the installer
   tar xzf ./actions-runner-osx-x64-2.311.0.tar.gz
   
   # Configure
   ./config.sh --url https://github.com/YOUR_USERNAME/devops-final-project \
     --token YOUR_REGISTRATION_TOKEN
   
   # Start the runner
   ./run.sh
   ```

3. **Keep the terminal open** (runner needs to be running)

   Or install as a service (optional):
   ```bash
   ./svc.sh install
   ./svc.sh start
   ```

### Step 2: Verify Runner is Connected

1. Go to: `https://github.com/YOUR_USERNAME/devops-final-project/settings/actions/runners`
2. You should see your runner with a **green dot** (online)

### Step 3: Make Sure K3d Cluster is Running

```bash
# Check cluster exists
k3d cluster list

# If not running, start it
k3d cluster start budget-cluster

# Or create new one
k3d cluster create budget-cluster --port "8889:80@loadbalancer"

# Verify
kubectl cluster-info
```

---

## 🎯 How to Use CD

### Scenario 1: You Change Code

```bash
# Edit your Flask code
vim app/main.py

# Commit and push
git add app/main.py
git commit -m "Add new feature"
git push origin main

# Watch GitHub Actions automatically:
# 1. Detect the push
# 2. Build new images
# 3. Import to K3d
# 4. Deploy to cluster
# 5. Rolling restart

# Check deployment at: http://localhost:8889
```

### Scenario 2: You Add New Service (nginx2)

```bash
# Create new K8s manifests
mkdir k8s/nginx2
vim k8s/nginx2/deployment.yml
vim k8s/nginx2/service.yml

# Commit and push
git add k8s/nginx2/
git commit -m "Add second nginx service"
git push origin main

# GitHub Actions automatically:
# 1. Detects new files in k8s/
# 2. Applies ALL manifests (including nginx2)
# 3. New service appears in cluster!

# Verify
kubectl get pods -n budget-app
# You'll see new nginx2 pods!
```

### Scenario 3: You Update K8s Config

```bash
# Change replica count
vim k8s/flask-app/deployment.yml
# Change replicas: 2 → 3

git add k8s/flask-app/deployment.yml
git commit -m "Scale flask to 3 replicas"
git push origin main

# Auto-deploys with new config!
```

---

## 📊 Watch Deployment in Real-Time

### In GitHub:
```
https://github.com/YOUR_USERNAME/devops-final-project/actions
```

You'll see:
- 🟡 Workflow running
- ✅ Each step completing
- 📝 Live logs

### In Terminal:
```bash
# Watch pods updating
kubectl get pods -n budget-app -w

# Watch deployment rollout
kubectl rollout status deployment/flask-app -n budget-app
```

---

## 🧪 Test Your CD

### Test 1: Code Change
```bash
# Make a simple change
echo "# CD Test" >> app/main.py
git add app/main.py
git commit -m "test: CD deployment"
git push

# Watch GitHub Actions run
# Check http://localhost:8889
```

### Test 2: New Service
```bash
# Create test service
mkdir -p k8s/test-service
cat > k8s/test-service/pod.yml << EOF
apiVersion: v1
kind: Pod
metadata:
  name: test-cd
  namespace: budget-app
spec:
  containers:
  - name: nginx
    image: nginx:alpine
EOF

git add k8s/test-service/
git commit -m "test: Add test service"
git push

# Verify it was deployed
kubectl get pod test-cd -n budget-app
# Should show Running!
```

---

## 🔍 Troubleshooting

### Runner Not Starting Workflow

**Check runner status:**
```bash
# Go to: Settings → Actions → Runners
# Should show green dot
```

**Restart runner:**
```bash
cd actions-runner
./run.sh
```

### Workflow Fails on K3d Commands

**Ensure K3d cluster is running:**
```bash
k3d cluster list
# Should show "budget-cluster" running

k3d cluster start budget-cluster
```

**Check kubectl access:**
```bash
kubectl cluster-info
# Should connect to K3d cluster
```

### Images Not Importing

**Pre-build images:**
```bash
docker-compose build
docker images | grep devops-final-project
# Should show your images
```

### Deployment Stuck

**Check logs:**
```bash
# GitHub Actions logs (web UI)
https://github.com/YOUR_USERNAME/devops-final-project/actions

# Pod logs
kubectl logs -f deployment/flask-app -n budget-app

# Events
kubectl get events -n budget-app --sort-by='.lastTimestamp'
```

---

## 🎓 For Your DevSecOps Presentation

### What to Show:

1. **Current State:**
   ```bash
   kubectl get pods -n budget-app
   ```

2. **Make a Change:**
   ```bash
   # Live edit
   echo "# Presentation demo" >> app/main.py
   git add app/main.py
   git commit -m "demo: Show CD in action"
   git push
   ```

3. **Show Automation:**
   - Open GitHub Actions tab
   - Show workflow running automatically
   - Show each step completing
   - Show updated pods

4. **Verify Deployment:**
   ```bash
   kubectl get pods -n budget-app
   # Show new pods with recent age
   
   curl http://localhost:8889/api/health
   # Show app is working
   ```

### What to Say:

> "I have implemented Continuous Deployment using GitHub Actions with a self-hosted runner. When I push code changes, the workflow automatically:
> 
> 1. Builds fresh Docker images
> 2. Imports them to the K3d cluster
> 3. Applies all Kubernetes manifests
> 4. Performs a rolling restart
> 
> This includes detecting new services - if I add a new nginx or any K8s resource, it's automatically deployed. The entire process takes about 30-60 seconds.
>
> For production, this would use a cloud-hosted runner and a proper image registry like GHCR or Docker Hub, but the workflow remains the same."

---

## 🎯 What Makes This CD?

| Characteristic | Your Setup |
|----------------|------------|
| **Automated** | ✅ No manual commands after push |
| **Triggered by Git** | ✅ Pushes to main branch |
| **Builds artifacts** | ✅ Docker images |
| **Deploys automatically** | ✅ To K3d cluster |
| **Handles new services** | ✅ Applies all manifests |
| **Idempotent** | ✅ Safe to run multiple times |
| **Shows status** | ✅ Deployment logs |

**This IS continuous deployment!** ✅

---

## 📝 Differences from Production CD

| Aspect | Your Setup | Production |
|--------|-----------|------------|
| **Runner** | Your laptop | Cloud runners / K8s Job |
| **Images** | Local only | Registry (GHCR/Docker Hub) |
| **Target** | Local K3d | Remote K8s cluster |
| **Versioning** | `:latest` tag | Commit SHA tags |
| **Rollback** | Manual | Automated (via ArgoCD) |

**For a learning project, your setup demonstrates all the CD concepts!**

---

## 🚀 Next Steps (Optional)

Want to make it more production-like?

1. **Add image registry** (GHCR - free & private)
2. **Add semantic versioning** (tag with commit SHA)
3. **Add deployment notifications** (Slack/email)
4. **Add smoke tests** (verify deployment after deploy)
5. **Add ArgoCD** (for GitOps comparison)

---

## 🆘 Need Help?

**Runner issues:**
- Check: `https://github.com/YOUR_USERNAME/devops-final-project/settings/actions/runners`
- Restart: `cd actions-runner && ./run.sh`

**Deployment issues:**
- Check workflow logs in GitHub Actions tab
- Check pod status: `kubectl get pods -n budget-app`
- Check events: `kubectl get events -n budget-app`

---

**You now have working Continuous Deployment!** 🎉

