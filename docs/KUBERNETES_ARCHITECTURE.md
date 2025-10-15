# 🏗️ Complete Project Architecture & Documentation

> **Comprehensive guide to understanding every file, component, and workflow in this DevOps project**

## 📑 Table of Contents

1. [Project Overview](#project-overview)
2. [Quick Start](#quick-start)
3. [Complete File Structure](#complete-file-structure)
4. [Architecture Diagrams](#architecture-diagrams)
5. [GitOps CI/CD Workflow](#gitops-cicd-workflow)
6. [Kubernetes Components](#kubernetes-components)
7. [Networking & Access](#networking--access)
8. [Monitoring Stack](#monitoring-stack)

---

## 🎯 Project Overview

**Budget App** - A full-stack DevOps project demonstrating:
- ✅ **CI/CD Pipeline** with GitHub Actions
- ✅ **GitOps** with automated manifest updates
- ✅ **Container Registry** (GitHub Container Registry)
- ✅ **Kubernetes Deployment** on K3d
- ✅ **ArgoCD** for GitOps continuous deployment
- ✅ **Multi-platform Docker builds** (amd64 + arm64)
- ✅ **Security scanning** with Trivy
- ✅ **Monitoring** with Prometheus & Grafana
- ✅ **PostgreSQL database** with persistent storage
- ✅ **Nginx reverse proxy**
- ✅ **Flask application** with JWT authentication

---

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/ChenBracha/devops-final-project.git
cd devops-final-project

# 2. Run the deployment script
python3 deploy.py

# 3. Access the services
# Budget App: http://localhost:8080
# ArgoCD UI: https://localhost:8443
#   Username: admin
#   Password: (shown in terminal output)
```

**That's it!** No manual port-forwarding or kubectl commands needed.

---

## 📂 Complete File Structure

### Root Directory

```
devops-final-project/
├── .github/workflows/       # CI/CD automation
│   └── ci-cd-gitops.yml    # Main GitHub Actions workflow
├── app/                     # Flask application source code
│   ├── __init__.py         # Python package marker
│   └── main.py             # Flask app with all routes & logic
├── argocd/                  # ArgoCD configuration
│   └── application.yaml    # ArgoCD Application manifest
├── docs/                    # Documentation
│   ├── DEPLOYMENT_WORKFLOW.md
│   ├── GITOPS_ARGOCD.md
│   ├── KUBERNETES_ARCHITECTURE.md (this file)
│   └── MONITORING.md
├── k8s/                     # Kubernetes manifests
│   ├── argocd-install.yml  # ArgoCD quick install (deprecated)
│   ├── flask-app/          # Flask application manifests
│   ├── ingress.yml         # Traefik ingress for direct access
│   ├── monitoring/         # Prometheus & Grafana manifests
│   ├── namespace.yml       # budget-app namespace
│   ├── nginx/              # Nginx reverse proxy manifests
│   └── postgres/           # PostgreSQL database manifests
├── monitoring/              # Monitoring configuration
│   ├── grafana/            # Grafana datasources & dashboards
│   └── prometheus.yml      # Prometheus configuration
├── nginx/                   # Nginx Docker build
│   ├── Dockerfile          # Custom nginx image
│   └── nginx.conf          # Nginx configuration
├── scripts/                 # Utility scripts (empty)
├── deploy.py               # **MAIN DEPLOYMENT SCRIPT** ⭐
├── Dockerfile              # Flask app Docker image
├── README.md               # Project README
├── requirements.txt        # Python dependencies
└── DEPLOYMENT.md           # Deployment instructions
```

---

## 🗂️ Detailed File Explanations

### 🎬 Main Entry Point

#### `deploy.py` ⭐ **START HERE**

**Purpose**: Automated deployment script that sets up everything.

**What it does**:
1. ✅ Checks Docker is running
2. ✅ Verifies `kubectl` and `k3d` are installed
3. ✅ Creates K3d cluster with port mappings (8080:80, 8443:443)
4. ✅ Installs ArgoCD
5. ✅ Exposes ArgoCD UI via LoadBalancer
6. ✅ Deploys application (PostgreSQL, Flask, Nginx)
7. ✅ Creates Traefik Ingress resources
8. ✅ Configures ArgoCD for insecure mode (behind ingress)
9. ✅ Retrieves & displays ArgoCD password
10. ✅ Shows access URLs (no port-forward needed)

**How to use**:
```bash
python3 deploy.py
```

**Requirements**:
- Docker Desktop running
- kubectl installed
- k3d installed
- Python 3.x

---

### 🐳 Application Source Code

#### `app/main.py`

**Purpose**: Main Flask application with all business logic.

**Features**:
- 🔐 **Authentication**: JWT + OAuth (Google)
- 👤 **Demo mode**: Try without authentication
- 💰 **Budget tracking**: Income, expenses, bills
- 📊 **Categories**: Customizable expense categories
- 💾 **Database**: PostgreSQL with SQLAlchemy ORM
- 📈 **Metrics**: Prometheus Flask Exporter
- 🏥 **Health endpoint**: `/api/health`

**Key Routes**:
```
/                    → Redirect to /budget
/login               → Login page
/budget              → Main budget app UI
/history             → Transaction history with charts
/api/health          → Health check {"status":"ok"}
/api/auth/register   → User registration (POST)
/api/auth/login      → User login (POST)
/auth/google         → Google OAuth login
/demo                → Demo mode (no auth)
/metrics             → Prometheus metrics
```

**Database Models**:
- `Family`: Family/group for budget sharing
- `User`: Users with email, password_hash, google_id
- `Category`: Budget categories with monthly limits
- `Transaction`: Income/expense/bill transactions

**Environment Variables**:
```bash
DATABASE_URL=postgresql+psycopg2://app:app@db:5432/app
JWT_SECRET_KEY=your-secret
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
SECRET_KEY=session-secret
```

---

#### `Dockerfile`

**Purpose**: Builds the Flask application Docker image.

**Build process**:
```dockerfile
FROM python:3.11-slim          # Base image
WORKDIR /app                   # Set working directory
COPY requirements.txt .        # Copy dependencies
RUN pip install ...            # Install packages
COPY ./app /app                # Copy application code
EXPOSE 5000                    # Expose Flask port
CMD ["gunicorn", ...]          # Run with Gunicorn WSGI
```

**Built by**: GitHub Actions CI/CD
**Pushed to**: `ghcr.io/chenbracha/devops-final-project:sha-XXXXXXX`
**Platforms**: linux/amd64, linux/arm64

---

#### `requirements.txt`

**Purpose**: Python dependencies for the Flask application.

**Key packages**:
```
Flask==3.0.3                    # Web framework
gunicorn==23.0.0                # WSGI server
psycopg2-binary==2.9.9          # PostgreSQL adapter
Flask-JWT-Extended==4.6.0       # JWT authentication
Flask-SQLAlchemy==3.1.1         # ORM
prometheus-flask-exporter==0.23.0  # Metrics
google-auth==2.23.4             # OAuth
flake8==7.1.0                   # Linting
```

---

### ⚙️ CI/CD Pipeline

#### `.github/workflows/ci-cd-gitops.yml`

**Purpose**: Automated CI/CD pipeline with GitOps manifest updates.

**Triggered by**: Push to `main` branch or Pull Requests

**Workflow Jobs**:

##### **Job 1: test-and-scan**
```yaml
Steps:
1. Checkout code
2. Setup Python 3.11
3. Install dependencies
4. Lint with Flake8 (check code quality)
5. Run Trivy filesystem scan (security vulnerabilities)
```

##### **Job 2: build-and-push** (only on push to main)
```yaml
Steps:
1. Checkout code
2. Setup Docker Buildx (multi-platform)
3. Login to GHCR (GitHub Container Registry)
4. Extract metadata (generate tags)
   - sha-XXXXXXX (commit SHA - immutable)
   - main (branch name)
   - latest (for default branch)
5. Build & push Docker image
   - Platforms: linux/amd64, linux/arm64
   - Cache: GitHub Actions cache
6. Calculate short SHA (7 characters)
7. Run Trivy on pushed image
8. **🔄 Update Kubernetes manifest**
   - Updates k8s/flask-app/deployment.yml
   - Changes image tag to sha-XXXXXXX
   - Commits with message: "chore: update image to sha-XXX [skip ci]"
   - Pushes back to repository
9. Generate build summary
```

**Environment Variables**:
```yaml
REGISTRY: ghcr.io
IMAGE_NAME: chenbracha/devops-final-project
```

**Permissions**:
```yaml
contents: write   # Push manifest updates
packages: write   # Push Docker images
```

**Key Innovation**: 
The workflow automatically updates the Kubernetes manifest after building the image, enabling true GitOps where Git is the single source of truth.

---

### 🚢 Kubernetes Manifests

#### `k8s/namespace.yml`

**Purpose**: Creates isolated namespace for the application.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: budget-app
```

**Why**: Isolates resources, enables RBAC, organizes deployments.

---

### 🔍 Namespace Architecture

**This project uses TWO namespaces:**

#### 1. `argocd` namespace
**Purpose**: Contains ArgoCD itself (the GitOps controller)

**Components**:
- `argocd-server` - Web UI and API
- `argocd-repo-server` - Git repository connection
- `argocd-application-controller` - Manages applications
- `argocd-redis` - Cache
- `argocd-dex-server` - SSO/Auth (optional)

**Why separate?**
- ✅ **Separation of concerns**: ArgoCD is the "operator" that manages applications, not part of the applications themselves
- ✅ **Security**: ArgoCD has elevated permissions to manage cluster resources
- ✅ **Lifecycle**: ArgoCD persists even if you delete application namespaces
- ✅ **Multi-tenancy**: One ArgoCD can manage multiple application namespaces
- ✅ **Best practice**: Standard pattern recommended by ArgoCD documentation

#### 2. `budget-app` namespace
**Purpose**: Contains your actual application and its dependencies

**Components**:
- Flask application
- PostgreSQL database
- Nginx reverse proxy
- Prometheus monitoring
- Grafana dashboards

**Why separate from ArgoCD?**
- ✅ **Clean separation**: Your app doesn't mix with ArgoCD infrastructure
- ✅ **Easy cleanup**: Delete namespace = delete entire app (without breaking ArgoCD)
- ✅ **Resource isolation**: Separate quotas, limits, and RBAC policies
- ✅ **Production-ready**: Mirrors real-world multi-namespace architecture

**Visualization**:
```
┌────────────────────────────────────────┐
│         K3d Cluster                     │
│                                         │
│  ┌──────────────────────────────────┐ │
│  │  argocd namespace                │ │
│  │  (The GitOps Controller)         │ │
│  │  - Watches Git                   │ │
│  │  - Manages deployments           │ │
│  │  - Provides UI                   │ │
│  └──────────┬───────────────────────┘ │
│             │ manages ↓               │
│  ┌──────────────────────────────────┐ │
│  │  budget-app namespace            │ │
│  │  (Your Application)              │ │
│  │  - Flask app                     │ │
│  │  - PostgreSQL                    │ │
│  │  - Nginx                         │ │
│  │  - Prometheus + Grafana          │ │
│  └──────────────────────────────────┘ │
└────────────────────────────────────────┘
```

---

#### `k8s/ingress.yml` ⭐ **NEW - Direct Browser Access**

**Purpose**: Exposes services via Traefik ingress (no port-forward needed).

**Budget App Ingress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: budget-app-ingress
  namespace: budget-app
spec:
  rules:
  - host: localhost
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-service
            port: 80
```
**Access**: `http://localhost:8080` → nginx-service:80

**ArgoCD Ingress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    traefik.ingress.kubernetes.io/router.entrypoints: websecure
    traefik.ingress.kubernetes.io/router.tls: "true"
spec:
  rules:
  - host: localhost
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port: 80
```
**Access**: `https://localhost:8443` → argocd-server:80

**How it works**:
1. K3d cluster created with port mappings: `8080:80` and `8443:443`
2. Ports map to Traefik LoadBalancer (K3d default ingress)
3. Traefik reads Ingress resources
4. Traefik routes traffic based on path/host rules
5. Users access services directly in browser

---

#### `k8s/postgres/` - PostgreSQL Database

##### `deployment.yml`
```yaml
Deployment: postgres
Replicas: 1
Image: postgres:15-alpine
Port: 5432
Resources:
  Requests: 256Mi RAM, 250m CPU
  Limits: 512Mi RAM, 500m CPU
Volume: postgres-pvc mounted at /var/lib/postgresql/data
Environment Variables:
  POSTGRES_USER: app (from secret)
  POSTGRES_PASSWORD: app (from secret)
  POSTGRES_DB: app (from secret)
Health Checks:
  Readiness: pg_isready (every 5s)
  Liveness: pg_isready (every 10s)
```

##### `service.yml`
```yaml
Service: postgres-service
Type: ClusterIP (internal only)
Port: 5432
Selector: app=postgres
```

##### `pv-pvc.yml`
```yaml
PersistentVolume: postgres-pv
Storage: 2Gi
AccessMode: ReadWriteOnce
StorageClass: local-path (K3d default)
HostPath: /tmp/k3d-postgres-data

PersistentVolumeClaim: postgres-pvc
Storage: 2Gi
StorageClass: local-path
```

**Note**: `local-path` is K3d's default storage class. Changed from `local-storage` to fix storage binding issues.

##### `secret.yml`
```yaml
Secret: postgres-secret
Type: Opaque
Data:
  POSTGRES_USER: YXBw (base64 "app")
  POSTGRES_PASSWORD: YXBw (base64 "app")
  POSTGRES_DB: YXBw (base64 "app")
  DATABASE_URL: postgresql://app:app@postgres-service:5432/app
```

**Security Note**: In production, use encrypted secrets (e.g., sealed-secrets, external-secrets).

---

#### `k8s/flask-app/` - Flask Application

##### `deployment.yml`
```yaml
Deployment: flask-app
Replicas: 2 (high availability)
Image: ghcr.io/chenbracha/devops-final-project:sha-XXXXXXX
ImagePullPolicy: Always
Port: 5000
Resources:
  Requests: 256Mi RAM, 250m CPU
  Limits: 512Mi RAM, 500m CPU
Environment Variables:
  DATABASE_URL: (from flask-secret)
  SECRET_KEY: (from flask-secret)
  FLASK_ENV: (from flask-secret)
  GOOGLE_CLIENT_ID: (from flask-secret)
  GOOGLE_CLIENT_SECRET: (from flask-secret)
Health Checks:
  Readiness: GET /api/health (every 5s, delay 10s)
  Liveness: GET /api/health (every 10s, delay 30s)
Init Container:
  Name: wait-for-postgres
  Image: postgres:15-alpine
  Command: pg_isready loop until PostgreSQL is ready
```

**Image Tag Format**: `sha-XXXXXXX` where XXXXXXX is the 7-char commit SHA.
**Why**: Immutable deployments - each commit gets unique image tag.

##### `service.yml`
```yaml
Service: flask-service
Type: ClusterIP (internal only)
Port: 5000
Selector: app=flask-app
```

##### `secret.yml`
```yaml
Secret: flask-secret
Type: Opaque
Data:
  DATABASE_URL: postgresql://...
  SECRET_KEY: your-secret-key
  FLASK_ENV: production
  GOOGLE_CLIENT_ID: (your OAuth client ID)
  GOOGLE_CLIENT_SECRET: (your OAuth secret)
```

---

#### `k8s/nginx/` - Nginx Reverse Proxy

##### `deployment.yml`
```yaml
Deployment: nginx
Replicas: 1
Image: nginx:stable-alpine
Port: 80
Resources:
  Requests: 64Mi RAM, 100m CPU
  Limits: 128Mi RAM, 200m CPU
Volume: nginx-config mounted at /etc/nginx/nginx.conf
Health Checks:
  Readiness: GET /nginx-health (every 5s)
  Liveness: GET /nginx-health (every 10s)
```

##### `service.yml`
```yaml
Service: nginx-service
Type: LoadBalancer (for K3d port mapping)
Port: 80
Selector: app=nginx
```

##### `configmap.yml`
```yaml
ConfigMap: nginx-config
Data: nginx.conf
Content:
  - Reverse proxy to flask-service:5000
  - Security headers
  - Health check endpoint /nginx-health
  - Timeouts: 60s
  - Client max body size: 10M
  - Access logging
```

**Nginx Configuration Highlights**:
```nginx
upstream flask_app {
    server flask-service:5000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://flask_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /nginx-health {
        return 200 "healthy\n";
    }
}
```

---

#### `k8s/monitoring/` - Prometheus & Grafana

**Location**: Both Prometheus and Grafana run in the `budget-app` namespace alongside your application.

**Why in budget-app namespace?**
- ✅ They monitor the budget-app specifically
- ✅ Deployed and managed together with the application
- ✅ Deleted together when cleaning up
- ✅ Can be easily scaled with the application

##### `prometheus-configmap.yml`
**Purpose**: Prometheus configuration file

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: prometheus-config
  namespace: budget-app
data:
  prometheus.yml: |
    global:
      scrape_interval: 15s
    
    scrape_configs:
      # Scrape Flask application metrics
      - job_name: 'flask-app'
        static_configs:
          - targets: ['flask-service:5000']
      
      # Scrape Nginx metrics
      - job_name: 'nginx'
        static_configs:
          - targets: ['nginx-service:80']
```

##### `prometheus-deployment.yml`
**Purpose**: Deploys Prometheus server

```yaml
Deployment: prometheus
  Replicas: 1
  Image: prom/prometheus:latest
  Port: 9090
  Volume: prometheus-config (ConfigMap)
  Resources:
    Requests: 256Mi RAM, 250m CPU
    Limits: 512Mi RAM, 500m CPU

Service: prometheus-service
  Type: ClusterIP
  Port: 9090
```

**Access**:
```bash
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090
# Open: http://localhost:9090
```

##### `grafana-configmap.yml`
**Purpose**: Grafana datasource and dashboard configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: budget-app
data:
  prometheus.yml: |
    datasources:
    - name: Prometheus
      type: prometheus
      access: proxy
      url: http://prometheus-service:9090
      isDefault: true
```

##### `grafana-deployment.yml`
**Purpose**: Deploys Grafana visualization platform

```yaml
Deployment: grafana
  Replicas: 1
  Image: grafana/grafana:latest
  Port: 3000
  ConfigMaps:
    - grafana-datasources (Prometheus connection)
    - grafana-dashboards (dashboard config)
  Environment:
    GF_AUTH_ANONYMOUS_ENABLED: true
    GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
  Resources:
    Requests: 128Mi RAM, 100m CPU
    Limits: 256Mi RAM, 200m CPU

Service: grafana-service
  Type: ClusterIP
  Port: 3000
```

**Access Grafana**:
```bash
kubectl port-forward -n budget-app svc/grafana-service 3000:3000
# Open: http://localhost:3000
# Login: admin/admin
```

**Pre-configured**:
- ✅ Prometheus datasource auto-configured
- ✅ Points to `prometheus-service:9090`
- ✅ Ready to create dashboards immediately

---

### 🔄 ArgoCD Configuration

#### `argocd/application.yaml`

**Purpose**: Defines ArgoCD Application for GitOps continuous deployment.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: budget-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  
  # Source: Git repository
  source:
    repoURL: https://github.com/ChenBracha/devops-final-project.git
    targetRevision: HEAD
    path: k8s
    directory:
      recurse: true  # Scan subdirectories
  
  # Destination: K3d cluster
  destination:
    server: https://kubernetes.default.svc
    namespace: budget-app
  
  # Sync Policy: Automated
  syncPolicy:
    automated:
      prune: true       # Delete removed resources
      selfHeal: true    # Auto-sync on drift
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
```

**How ArgoCD Works**:
1. 📊 Polls Git repository every 3 minutes (default)
2. 🔍 Detects changes in `k8s/` directory
3. 🔄 Compares desired state (Git) vs actual state (K8s)
4. ⚡ Auto-syncs if `automated.selfHeal: true`
5. ✅ Updates Kubernetes resources
6. 🏥 Marks application as "Healthy" and "Synced"

---

## 🏗️ Architecture Diagrams

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER'S BROWSER                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  http://localhost:8080          https://localhost:8443              │
│  (Budget App)                   (ArgoCD UI)                          │
│                                                                       │
└──────────┬───────────────────────────────────────────┬──────────────┘
           │                                           │
           ▼                                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        K3D CLUSTER                                   │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              TRAEFIK INGRESS CONTROLLER                       │  │
│  │  (Default K3d LoadBalancer)                                   │  │
│  │  Ports: 80 (→8080), 443 (→8443)                               │  │
│  └───┬──────────────────────────────────────────────────────┬───┘  │
│      │                                                       │       │
│      │ /                                                     │ /     │
│      ▼                                                       ▼       │
│  ┌─────────────────────────┐              ┌──────────────────────┐ │
│  │  budget-app namespace   │              │  argocd namespace    │ │
│  ├─────────────────────────┤              ├──────────────────────┤ │
│  │                         │              │                      │ │
│  │ ┌─────────────────────┐ │              │ ┌─────────────────┐│ │
│  │ │  nginx-service      │ │              │ │ argocd-server   ││ │
│  │ │  (ClusterIP)        │ │              │ │ (LoadBalancer)  ││ │
│  │ │  Port: 80           │ │              │ │ Port: 80/443    ││ │
│  │ └──────────┬──────────┘ │              │ └─────────────────┘│ │
│  │            │             │              │                      │ │
│  │            ▼             │              └──────────────────────┘ │
│  │ ┌─────────────────────┐ │                                        │
│  │ │  flask-service      │ │                                        │
│  │ │  (ClusterIP)        │ │                                        │
│  │ │  Port: 5000         │ │                                        │
│  │ │  Replicas: 2        │ │                                        │
│  │ └──────────┬──────────┘ │                                        │
│  │            │             │                                        │
│  │            ▼             │                                        │
│  │ ┌─────────────────────┐ │                                        │
│  │ │  postgres-service   │ │                                        │
│  │ │  (ClusterIP)        │ │                                        │
│  │ │  Port: 5432         │ │                                        │
│  │ │  Replicas: 1        │ │                                        │
│  │ │  Volume: PVC 2Gi    │ │                                        │
│  │ └─────────────────────┘ │                                        │
│  │                         │                                        │
│  │ Monitoring:             │                                        │
│  │ - Prometheus (9090)     │                                        │
│  │ - Grafana (3000)        │                                        │
│  └─────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

### GitOps CI/CD Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DEVELOPER WORKFLOW                                │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  1. Code Change │
                    │  git push main  │
                    └────────┬────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS CI/CD                              │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Job 1: test-and-scan                                         │ │
│  │  • Checkout code                                              │ │
│  │  • Setup Python                                               │ │
│  │  • Install dependencies                                       │ │
│  │  • Lint with Flake8                                           │ │
│  │  • Security scan with Trivy (filesystem)                      │ │
│  └────────────────────────────┬─────────────────────────────────┘ │
│                               │                                    │
│                               ▼                                    │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Job 2: build-and-push (only if Job 1 passes)                │ │
│  │  • Checkout code                                              │ │
│  │  • Setup Docker Buildx                                        │ │
│  │  • Login to GHCR                                              │ │
│  │  • Extract metadata                                           │ │
│  │  • Build multi-platform image:                                │ │
│  │    - linux/amd64                                              │ │
│  │    - linux/arm64                                              │ │
│  │  • Tag: ghcr.io/chenbracha/.../project:sha-XXXXXXX           │ │
│  │  • Push to registry                                           │ │
│  │  • Security scan with Trivy (Docker image)                    │ │
│  │  • Calculate short SHA                                        │ │
│  │                                                                │ │
│  │  🔄 **GITOPS MAGIC - Automatic Manifest Update**              │ │
│  │  • Update k8s/flask-app/deployment.yml                        │ │
│  │  • Change image tag to sha-XXXXXXX                            │ │
│  │  • Commit: "chore: update image to sha-XXX [skip ci]"        │ │
│  │  • Push back to repository                                    │ │
│  └────────────────────────────┬─────────────────────────────────┘ │
└────────────────────────────────┼──────────────────────────────────┘
                                 │
                                 │ Git commit pushed
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                          GIT REPOSITORY                             │
│  k8s/flask-app/deployment.yml updated with new image tag           │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             │ ArgoCD polls every 3 min
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                          ARGOCD                                     │
├────────────────────────────────────────────────────────────────────┤
│  1. Detects manifest change in Git                                 │
│  2. Compares desired state (Git) vs actual state (K8s)            │
│  3. Triggers sync (automatic if selfHeal: true)                    │
│  4. Pulls new image: ghcr.io/.../project:sha-XXXXXXX               │
│  5. Performs rolling update (2 replicas)                           │
│  6. Validates health checks                                        │
│  7. Marks application: Healthy ✅ Synced ✅                         │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER (K3D)                         │
│  New version of app deployed! 🎉                                   │
│  URL: http://localhost:8080                                        │
└────────────────────────────────────────────────────────────────────┘
```

**Key Points**:
- ✅ **Immutable deployments**: Each commit gets unique SHA tag
- ✅ **Automated updates**: No manual kubectl apply needed
- ✅ **Audit trail**: All changes tracked in Git
- ✅ **Rollback**: `git revert` + ArgoCD auto-syncs
- ✅ **Security**: Trivy scans at multiple stages

---

## 🌐 Networking & Access

### Port Mappings

**K3d Cluster Creation**:
```bash
k3d cluster create budget-cluster \
  --port '8080:80@loadbalancer' \
  --port '8443:443@loadbalancer'
```

This maps:
- Host `localhost:8080` → K3d LoadBalancer port 80 (HTTP)
- Host `localhost:8443` → K3d LoadBalancer port 443 (HTTPS)

### Traefik Ingress Flow

```
User Browser
    │
    ├─ http://localhost:8080
    │      │
    │      ▼
    │  Host Port 8080
    │      │
    │      ▼
    │  K3d LB Port 80
    │      │
    │      ▼
    │  Traefik Ingress Controller
    │      │
    │      ▼ (Ingress Rule: host=localhost, path=/)
    │  nginx-service:80
    │      │
    │      ▼ (Nginx Proxy)
    │  flask-service:5000
    │      │
    │      ▼
    │  Flask App Pods
    │
    └─ https://localhost:8443
           │
           ▼
       Host Port 8443
           │
           ▼
       K3d LB Port 443
           │
           ▼
       Traefik Ingress Controller
           │
           ▼ (Ingress Rule: host=localhost, path=/, TLS)
       argocd-server:80
           │
           ▼
       ArgoCD Server Pod
```

### Service Types Explained

| Service Type | Purpose | External Access |
|--------------|---------|-----------------|
| **ClusterIP** | Internal only | No (default) |
| **LoadBalancer** | External via LB | Yes (K3d maps to host) |
| **Ingress** | HTTP/HTTPS routing | Yes (via Traefik) |

**Our Setup**:
- `nginx-service`: LoadBalancer (for ingress routing)
- `flask-service`: ClusterIP (internal only)
- `postgres-service`: ClusterIP (internal only)
- `argocd-server`: LoadBalancer (for ingress routing)

**Access Methods**:
1. ✅ **Direct Browser** (via Ingress): `http://localhost:8080`
2. ❌ **Port Forward** (not needed): `kubectl port-forward svc/flask-service 5000:5000`

---

## 📊 Monitoring Stack

### Prometheus

**Purpose**: Metrics collection and time-series database.

**Targets**:
- `flask-service:5000` - Flask app metrics (via prometheus-flask-exporter)
- `nginx-service:80` - Nginx stub_status
- Kubernetes API server
- K3d node metrics

**Metrics Collected**:
```
# Flask App
flask_http_request_total
flask_http_request_duration_seconds
flask_http_request_exceptions_total

# Nginx
nginx_connections_active
nginx_requests_total

# System
container_cpu_usage_seconds_total
container_memory_working_set_bytes
```

**Access**:
```bash
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090
# Open: http://localhost:9090
```

### Grafana

**Purpose**: Visualization and dashboards.

**Datasources**: Prometheus (auto-configured)

**Dashboards**:
- Application metrics (requests, latency, errors)
- System resources (CPU, RAM, disk)
- Database connections
- Nginx traffic

**Access**:
```bash
kubectl port-forward -n budget-app svc/grafana-service 3000:3000
# Open: http://localhost:3000
# Login: admin/admin
```

**Pre-configured**:
- Datasource: `prometheus-datasources` ConfigMap
- Dashboards: `grafana-dashboards` ConfigMap

---

## 🔐 Security Considerations

### Current Security Measures

✅ **Implemented**:
1. **Namespace isolation** - Resources in separate namespaces
2. **Secrets management** - Sensitive data in Kubernetes Secrets
3. **Image scanning** - Trivy scans for vulnerabilities
4. **Resource limits** - CPU/RAM limits prevent resource exhaustion
5. **Health checks** - Automatic pod restarts on failure
6. **Non-root containers** - Flask runs as non-root user
7. **Nginx security headers** - X-Frame-Options, X-XSS-Protection
8. **JWT authentication** - Secure API access
9. **OAuth integration** - Google authentication
10. **Network policies** - ArgoCD has network policies

### Production Improvements Needed

⚠️ **TODO for Production**:
1. **Encrypt secrets** - Use sealed-secrets or external-secrets-operator
2. **TLS certificates** - Use cert-manager for Let's Encrypt
3. **Network policies** - Restrict pod-to-pod communication
4. **RBAC** - Fine-grained access control
5. **Pod Security Standards** - Enforce restricted PSS
6. **Image signing** - Use cosign for image verification
7. **Audit logging** - Enable Kubernetes audit logs
8. **Backup strategy** - Regular database backups
9. **Disaster recovery** - Test restore procedures
10. **Vulnerability patching** - Regular image updates

---

## 🧪 Testing the Complete Flow

### Test GitOps Workflow

```bash
# 1. Make a code change
echo "# Test change" >> app/main.py

# 2. Commit and push
git add app/main.py
git commit -m "test: verify GitOps workflow"
git push origin main

# 3. Watch GitHub Actions
# Visit: https://github.com/ChenBracha/devops-final-project/actions

# 4. After 2-3 minutes, check the manifest update
git pull origin main
cat k8s/flask-app/deployment.yml | grep image:
# Should show new sha-XXXXXXX tag

# 5. Check ArgoCD (auto-syncs every 3 min)
# Visit: https://localhost:8443
# Or force sync in UI

# 6. Verify new pods
kubectl get pods -n budget-app
kubectl describe deployment flask-app -n budget-app | grep Image:

# 7. Test the app
curl http://localhost:8080/api/health
```

### Test Application Features

```bash
# Health check
curl http://localhost:8080/api/health

# Prometheus metrics
curl http://localhost:8080/metrics

# Web UI
open http://localhost:8080/budget

# Demo mode (no auth)
open http://localhost:8080/demo

# Google OAuth login
open http://localhost:8080/login
```

### Test Monitoring

```bash
# Prometheus targets
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090
open http://localhost:9090/targets

# Grafana dashboards
kubectl port-forward -n budget-app svc/grafana-service 3000:3000
open http://localhost:3000
# Login: admin/admin
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **Pods not starting**

```bash
# Check pod status
kubectl get pods -n budget-app

# Check events
kubectl describe pod <pod-name> -n budget-app

# Check logs
kubectl logs <pod-name> -n budget-app

# Common causes:
# - Image pull errors (check GHCR access)
# - Resource limits (check node resources)
# - Init container failures (check PostgreSQL)
```

#### 2. **Application not accessible**

```bash
# Check ingress
kubectl get ingress -A

# Check Traefik
kubectl get svc -n kube-system traefik

# Check port mappings
docker ps | grep k3d-budget-cluster-serverlb

# Test internal connectivity
kubectl run -it --rm debug --image=alpine --restart=Never -n budget-app -- sh
# Inside pod:
wget -qO- http://nginx-service
```

#### 3. **ArgoCD not syncing**

```bash
# Check ArgoCD application status
kubectl get application budget-app -n argocd

# Check ArgoCD logs
kubectl logs -n argocd deployment/argocd-server

# Force refresh
kubectl patch application budget-app -n argocd \
  --type merge -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

# Manual sync
kubectl patch application budget-app -n argocd \
  --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

#### 4. **Database connection errors**

```bash
# Check PostgreSQL pod
kubectl get pod -l app=postgres -n budget-app

# Check PostgreSQL logs
kubectl logs -l app=postgres -n budget-app

# Check PVC
kubectl get pvc -n budget-app

# Test connection from Flask pod
kubectl exec -it deployment/flask-app -n budget-app -- sh
# Inside pod:
python -c "import psycopg2; conn = psycopg2.connect('postgresql://app:app@postgres-service:5432/app'); print('OK')"
```

#### 5. **CI/CD workflow failing**

```bash
# Check GitHub Actions
# Visit: https://github.com/ChenBracha/devops-final-project/actions

# Common issues:
# - Flake8 linting errors → Fix code style
# - Trivy vulnerabilities → Update dependencies
# - Docker build fails → Check Dockerfile
# - GHCR push fails → Check repository settings
# - Manifest update fails → Check contents:write permission
```

---

## 📚 Additional Resources

### Documentation

- [Deployment Workflow](./DEPLOYMENT_WORKFLOW.md) - Step-by-step deployment guide
- [GitOps with ArgoCD](./GITOPS_ARGOCD.md) - ArgoCD configuration & usage
- [Monitoring Setup](./MONITORING.md) - Prometheus & Grafana details
- [Main README](../README.md) - Project overview

### External Links

- [K3d Documentation](https://k3d.io/)
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [GHCR Documentation](https://docs.github.com/en/packages)

---

## 🎓 Learning Outcomes

By completing this project, you've learned:

✅ **CI/CD**
- GitHub Actions workflows
- Multi-stage pipelines
- Automated testing & linting
- Security scanning with Trivy

✅ **Docker & Containers**
- Multi-platform builds
- Container registries (GHCR)
- Image tagging strategies
- Resource optimization

✅ **Kubernetes**
- Deployments, Services, ConfigMaps, Secrets
- Persistent storage (PV/PVC)
- Health checks & probes
- Resource requests & limits
- Ingress controllers
- Namespaces & isolation

✅ **GitOps**
- Git as single source of truth
- Automated manifest updates
- Declarative configuration
- ArgoCD continuous deployment

✅ **Networking**
- Service discovery
- Ingress routing
- Load balancing
- Port mappings

✅ **Monitoring**
- Prometheus metrics collection
- Grafana visualization
- Application instrumentation

✅ **DevOps Best Practices**
- Infrastructure as Code
- Immutable deployments
- Automated rollbacks
- Security scanning
- Documentation

---

## 🎉 Conclusion

This project demonstrates a **production-grade DevOps pipeline** with:

- ✅ Full automation from code push to deployment
- ✅ GitOps principles with ArgoCD
- ✅ Multi-platform container builds
- ✅ Security scanning at multiple stages
- ✅ Monitoring & observability
- ✅ Easy local development with K3d
- ✅ **Direct browser access - no manual commands!**

**Next Steps**:
1. 🔐 Add production-grade secrets management
2. 🌐 Deploy to cloud (AWS/GCP/Azure)
3. 📊 Add more Grafana dashboards
4. 🧪 Add integration tests
5. 📦 Implement Helm charts
6. 🔄 Add blue-green deployments
7. 🔐 Implement RBAC policies
8. 📝 Add API documentation (Swagger)

---

**Made with ❤️ for learning DevOps**

**Author**: Chen Bracha  
**Repository**: https://github.com/ChenBracha/devops-final-project  
**Last Updated**: October 2025
