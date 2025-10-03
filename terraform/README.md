# 🌩️ GCP Deployment with Terraform

This directory contains Infrastructure as Code (IaC) to deploy the Budget App to Google Cloud Platform using GKE (Google Kubernetes Engine).

## 📋 Prerequisites

### 1. Install Required Tools

```bash
# Install Terraform
brew install terraform

# Install Google Cloud SDK
brew install google-cloud-sdk

# Verify installations
terraform --version
gcloud --version
```

### 2. GCP Account Setup

1. **Create/Login to GCP Account**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - New accounts get **$300 free credits** (90 days)

2. **Create a New Project**
   ```bash
   gcloud projects create YOUR-PROJECT-ID --name="Budget App"
   ```

3. **Set Default Project**
   ```bash
   gcloud config set project YOUR-PROJECT-ID
   ```

4. **Enable Billing**
   - Go to console.cloud.google.com/billing
   - Link your project to billing account
   - *Note: You won't be charged if using free credits*

5. **Authenticate**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

---

## 🚀 Deployment Steps

### Step 1: Configure Variables

```bash
# Copy example file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**Required variables:**
```hcl
project_id  = "your-gcp-project-id"     # Your GCP project
db_password = "secure-password-here"     # Database password
```

### Step 2: Initialize Terraform

```bash
terraform init
```

This downloads the required providers (Google Cloud).

### Step 3: Plan Deployment

```bash
terraform plan
```

This shows what will be created:
- ✅ VPC network and subnet
- ✅ GKE cluster (2 nodes, e2-small)
- ✅ Cloud SQL PostgreSQL instance
- ✅ Service accounts and IAM roles
- ✅ Firewall rules

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

⏱️ **This takes ~10-15 minutes** (GKE cluster creation is slow)

### Step 5: Configure kubectl

After successful deployment, connect to your cluster:

```bash
# Get the command from outputs
terraform output kubectl_connection_command

# Or directly:
gcloud container clusters get-credentials budget-app-cluster \
  --zone=us-central1-a \
  --project=YOUR-PROJECT-ID

# Verify connection
kubectl get nodes
```

### Step 6: Update K8s Secrets with DB Info

```bash
# Get database connection details
terraform output db_private_ip
terraform output db_password

# Update k8s/postgres/secret.yml with these values
# Or create a new secret specifically for Cloud SQL
```

### Step 7: Deploy Application to GKE

```bash
# From project root
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/flask-app/
kubectl apply -f k8s/nginx/
kubectl apply -f k8s/monitoring/

# Check deployment status
kubectl get pods -n budget-app
```

### Step 8: Get External IP

```bash
kubectl get service nginx-service -n budget-app

# Wait for EXTERNAL-IP (may take 2-3 minutes)
# Once assigned, access your app at:
# http://<EXTERNAL-IP>
```

---

## 💰 Cost Estimation

### With Free Tier ($300 credits):
- **First 90 days**: FREE (using credits)
- **Credits remaining**: Check in GCP console

### Without Free Tier:
| Resource | Monthly Cost |
|----------|--------------|
| GKE Cluster (2x e2-small) | ~$70 |
| Cloud SQL (db-f1-micro) | ~$10 |
| Load Balancer | ~$20 |
| **Total** | **~$100/month** |

### 💡 Cost Saving Tips:
```bash
# Destroy resources when not in use
terraform destroy

# Or scale down to 0 nodes (keeps cluster, reduces cost)
gcloud container clusters resize budget-app-cluster \
  --num-nodes=0 \
  --zone=us-central1-a
```

---

## 🗑️ Teardown / Cleanup

### To destroy ALL resources:

```bash
terraform destroy
```

Type `yes` to confirm.

⚠️ **This will delete:**
- GKE cluster
- Cloud SQL database (and all data!)
- VPC network
- Load balancer
- Everything created by Terraform

---

## 📁 File Structure

```
terraform/
├── main.tf                   # GKE cluster configuration
├── database.tf               # Cloud SQL PostgreSQL
├── variables.tf              # Input variables
├── outputs.tf                # Output values after deployment
├── terraform.tfvars.example  # Example configuration
├── terraform.tfvars          # Your actual config (gitignored)
├── .gitignore                # Ignore sensitive files
└── README.md                 # This file
```

---

## 🔐 Security Notes

### Secrets Management

**terraform.tfvars contains sensitive data!**
- ✅ Already in .gitignore
- ✅ Never commit this file
- ✅ Use different passwords for dev/prod

### Production Improvements:
```hcl
# In main.tf, for production:
deletion_protection = true       # Prevent accidental deletion
require_ssl         = true       # Force SSL for database
availability_type   = "REGIONAL" # High availability
```

---

## 🔧 Troubleshooting

### Error: API not enabled

```bash
# Enable required APIs manually
gcloud services enable container.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable servicenetworking.googleapis.com
```

### Error: Quota exceeded

- Check your GCP quotas in console
- Request quota increase if needed
- Or use smaller machine types

### Can't connect to cluster

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Get credentials again
gcloud container clusters get-credentials budget-app-cluster \
  --zone=us-central1-a
```

### Terraform state locked

```bash
# If terraform crashes mid-operation
# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>
```

---

## 📊 Monitoring Your Deployment

### GCP Console:
- **GKE**: console.cloud.google.com/kubernetes
- **Cloud SQL**: console.cloud.google.com/sql
- **Billing**: console.cloud.google.com/billing

### CLI Commands:
```bash
# Check cluster status
gcloud container clusters list

# Check database
gcloud sql instances list

# Check current costs
gcloud billing accounts list
```

---

## 🎯 Next Steps

After deployment:

1. ✅ Set up custom domain (optional)
2. ✅ Configure SSL/TLS certificate
3. ✅ Set up Cloud Monitoring alerts
4. ✅ Configure backup schedule
5. ✅ Add CI/CD pipeline (GitHub Actions)

---

## 📚 Resources

- [Terraform GCP Provider Docs](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [GCP Free Tier](https://cloud.google.com/free)

---

## 🆘 Support

- **Terraform Issues**: [terraform.io/docs](https://www.terraform.io/docs)
- **GCP Issues**: [cloud.google.com/support](https://cloud.google.com/support)
- **Project Issues**: Open an issue on GitHub

---

**Made with ❤️ for learning DevOps and Cloud Infrastructure**


