# ☁️ GCP Deployment Guide

Complete guide to deploying the Budget App to Google Cloud Platform using Terraform and GKE.

## 🎯 Overview

This guide will help you deploy your application to production on Google Cloud Platform using:
- **Terraform** - Infrastructure as Code
- **GKE** - Google Kubernetes Engine (managed Kubernetes)
- **Cloud SQL** - Managed PostgreSQL database
- **GitHub Actions** - Automated deployment

---

## 📋 Prerequisites Checklist

### Required Tools
- [ ] Google Cloud account ([console.cloud.google.com](https://console.cloud.google.com))
- [ ] Terraform installed (`brew install terraform`)
- [ ] Google Cloud SDK installed (`brew install google-cloud-sdk`)
- [ ] kubectl installed (`brew install kubectl`)
- [ ] GitHub account (for CI/CD)

### Cost Awareness
- ✅ New GCP accounts get **$300 free credits** (90 days)
- ✅ Estimated cost: ~$100/month (FREE with credits)
- ✅ Can destroy resources anytime to stop charges

---

## 🚀 Part 1: Infrastructure Setup with Terraform

### Step 1: GCP Account Setup

```bash
# 1. Login to GCP
gcloud auth login

# 2. Create a new project (or use existing)
gcloud projects create budget-app-12345 --name="Budget App Production"

# 3. Set as default project
gcloud config set project budget-app-12345

# 4. Enable billing (required even with free credits)
# Go to: console.cloud.google.com/billing
# Link your project to billing account

# 5. Enable required APIs
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable servicenetworking.googleapis.com
```

### Step 2: Configure Terraform

```bash
# Navigate to terraform directory
cd terraform/

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**terraform.tfvars:**
```hcl
project_id  = "budget-app-12345"        # Your GCP project ID
db_password = "super-secure-password"   # Choose a strong password
region      = "us-central1"            # Optional: change region
zone        = "us-central1-a"          # Optional: change zone
```

### Step 3: Deploy Infrastructure

```bash
# Initialize Terraform
terraform init

# See what will be created
terraform plan

# Deploy! (takes ~10-15 minutes)
terraform apply
```

Type `yes` when prompted.

**What gets created:**
- ✅ VPC network with subnets
- ✅ GKE cluster (2 nodes, e2-small)
- ✅ Cloud SQL PostgreSQL instance
- ✅ Service accounts and IAM roles
- ✅ Networking and firewall rules

### Step 4: Save Important Information

```bash
# Get cluster connection command
terraform output kubectl_connection_command

# Get database details
terraform output db_private_ip
terraform output db_password

# Save these for later!
```

---

## 📦 Part 2: Deploy Application to GKE

### Step 1: Connect to Cluster

```bash
# Use the command from terraform output
gcloud container clusters get-credentials budget-app-cluster \
  --zone=us-central1-a \
  --project=budget-app-12345

# Verify connection
kubectl get nodes
```

You should see 2 nodes running!

### Step 2: Update Database Configuration

Since we're using Cloud SQL, update your Kubernetes secrets:

```bash
# Get database IP
DB_IP=$(terraform output -raw db_private_ip)
DB_PASS=$(terraform output -raw db_password)

# Create/update database secret
kubectl create namespace budget-app

kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_PASSWORD=$DB_PASS \
  --from-literal=DATABASE_URL="postgresql+psycopg2://app:$DB_PASS@$DB_IP:5432/app" \
  -n budget-app \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Step 3: Deploy Application

```bash
# From project root
cd ..

# Deploy namespace
kubectl apply -f k8s/namespace.yml

# Skip PostgreSQL deployment (using Cloud SQL instead)
# kubectl apply -f k8s/postgres/  # Skip this!

# Deploy Flask app
kubectl apply -f k8s/flask-app/

# Deploy Nginx
kubectl apply -f k8s/nginx/

# Deploy monitoring (optional)
kubectl apply -f k8s/monitoring/
```

### Step 4: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n budget-app

# Should show:
# flask-app-xxx   Running
# nginx-xxx       Running
# prometheus-xxx  Running
# grafana-xxx     Running

# Wait for all pods to be ready
kubectl wait --for=condition=ready pod --all -n budget-app --timeout=300s
```

### Step 5: Get External IP

```bash
# Get service information
kubectl get service nginx-service -n budget-app

# Wait for EXTERNAL-IP (may take 2-3 minutes)
# Keep running this until you see an IP instead of <pending>
```

**Example output:**
```
NAME            TYPE           EXTERNAL-IP      PORT(S)
nginx-service   LoadBalancer   34.123.45.67     80:30000/TCP
```

### Step 6: Access Your App! 🎉

```bash
# Get the IP
EXTERNAL_IP=$(kubectl get service nginx-service -n budget-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Your app is running at: http://$EXTERNAL_IP"

# Open in browser
open "http://$EXTERNAL_IP"
```

---

## 🤖 Part 3: CI/CD with GitHub Actions

### Step 1: Create Service Account for GitHub

```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding budget-app-12345 \
  --member="serviceAccount:github-actions@budget-app-12345.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding budget-app-12345 \
  --member="serviceAccount:github-actions@budget-app-12345.iam.gserviceaccount.com" \
  --role="roles/container.clusterViewer"

# Create and download key
gcloud iam service-accounts keys create github-key.json \
  --iam-account=github-actions@budget-app-12345.iam.gserviceaccount.com

# This creates github-key.json - you'll need this!
```

### Step 2: Add Secrets to GitHub

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `GCP_PROJECT_ID` | `budget-app-12345` |
| `GCP_SA_KEY` | Contents of `github-key.json` file |
| `GKE_CLUSTER_NAME` | `budget-app-cluster` |
| `GKE_ZONE` | `us-central1-a` |

**To copy github-key.json:**
```bash
cat github-key.json | pbcopy  # macOS
# Or just open the file and copy contents
```

### Step 3: Test GitHub Actions Deployment

1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Deploy to GCP GKE" workflow
4. Click "Run workflow"
5. Type `deploy` in the confirmation field
6. Click "Run workflow"

Watch the deployment progress in real-time!

---

## 🔍 Monitoring & Troubleshooting

### Check Logs

```bash
# Flask app logs
kubectl logs -f deployment/flask-app -n budget-app

# Nginx logs
kubectl logs -f deployment/nginx -n budget-app

# All pods
kubectl logs -f -l app=flask-app -n budget-app
```

### Check Database Connection

```bash
# Connect to Flask pod
kubectl exec -it deployment/flask-app -n budget-app -- /bin/bash

# Inside pod, test database
python3 -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Database connection successful!')
"
```

### Access Monitoring

```bash
# Port-forward Grafana
kubectl port-forward -n budget-app svc/grafana-service 3000:3000

# Access at http://localhost:3000
# Login: admin / admin
```

### Common Issues

**Pods stuck in Pending:**
```bash
# Check events
kubectl get events -n budget-app --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n budget-app
```

**Can't connect to database:**
```bash
# Verify Cloud SQL private IP
terraform output db_private_ip

# Check secret
kubectl get secret postgres-secret -n budget-app -o yaml
```

**External IP stuck on <pending>:**
```bash
# Check load balancer status
kubectl describe service nginx-service -n budget-app

# Usually takes 2-3 minutes, be patient!
```

---

## 💰 Cost Management

### Check Current Costs

```bash
# Via CLI
gcloud billing accounts list

# Or visit:
open https://console.cloud.google.com/billing
```

### Reduce Costs

**Option 1: Scale down nodes to 0 (keeps cluster)**
```bash
gcloud container clusters resize budget-app-cluster \
  --num-nodes=0 \
  --zone=us-central1-a
```

**Option 2: Destroy everything**
```bash
cd terraform/
terraform destroy

# Type 'yes' to confirm
```

---

## 🎓 What You've Accomplished

✅ **Infrastructure as Code** - Terraform manages all GCP resources
✅ **Cloud Kubernetes** - Production-grade GKE deployment  
✅ **Managed Database** - Cloud SQL PostgreSQL
✅ **Load Balancing** - Automatic with GKE
✅ **CI/CD Pipeline** - GitHub Actions for automated deployment
✅ **Monitoring** - Prometheus + Grafana in production
✅ **Security** - Private networking, service accounts, IAM roles

---

## 📊 Architecture Diagram

```
GitHub (Code Push)
       ↓
GitHub Actions (CI/CD)
       ↓
GKE Cluster (2 nodes)
├── Nginx (LoadBalancer)  ←→  Internet
├── Flask App (3 replicas)
├── Prometheus
└── Grafana
       ↓
Cloud SQL PostgreSQL
(Private Network)
```

---

## 🎤 For Your Presentation

### Key Points to Highlight:

1. **Multi-environment deployment:**
   - Local development (Docker Compose)
   - Local Kubernetes (K3d)
   - Production cloud (GCP/GKE)

2. **Infrastructure as Code:**
   - All infrastructure defined in Terraform
   - Reproducible and version-controlled
   - Can recreate entire environment in minutes

3. **Production-ready features:**
   - Managed Kubernetes (GKE)
   - Managed database (Cloud SQL)
   - Auto-scaling nodes
   - High availability
   - Monitoring and observability

4. **DevOps best practices:**
   - CI/CD pipeline
   - Automated deployments
   - Security (service accounts, IAM)
   - Cost optimization

### Demo Flow (5 minutes):

1. Show Terraform code → "Infrastructure as Code"
2. Run `terraform plan` → "Preview changes"
3. Show GCP console → "Live infrastructure"
4. Show GitHub Actions → "Automated deployment"
5. Access app via External IP → "Running in production!"
6. Show Grafana → "Monitoring and metrics"

---

## 🧹 Cleanup After Project

**Important:** Don't forget to destroy resources after grading!

```bash
cd terraform/
terraform destroy
```

This:
- ✅ Deletes all GCP resources
- ✅ Stops all charges
- ✅ Preserves your free credits for future use
- ✅ You can always recreate with `terraform apply`

---

## 📚 Additional Resources

- [Terraform GCP Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Cloud SQL Documentation](https://cloud.google.com/sql/docs)
- [GCP Free Tier](https://cloud.google.com/free)

---

**Congratulations! You've deployed a production-grade application to the cloud!** 🎉


