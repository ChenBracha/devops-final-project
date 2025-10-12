# Israeli Budget App 💰🇮🇱

> A family budget management application with dual deployment architecture (Docker Compose + Kubernetes)

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Supported-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

A production-ready family budget management application built with Flask, featuring Google OAuth authentication, demo mode, and **dual deployment options**: Docker Compose (local dev) and K3d (local Kubernetes).

## ✨ Features

- 🔐 **Google OAuth Authentication** - Sign in with your Google account
- 🎭 **Demo Mode** - Try the app without registration
- 👨‍👩‍👧‍👦 **Family Budget Sharing** - Share budgets with family members
- 💰 **Israeli Shekel (₪) Support** - Native currency support for Israeli users
- 📊 **Transaction Management** - Track income, expenses, and bills
- 📈 **Visual Analytics** - Pie charts and spending breakdowns
- 📅 **Date Filtering** - Filter transactions by date range
- 🗑️ **Transaction Deletion** - Edit your budget history
- 🎨 **Modern UI** - Clean, responsive design
- 🔒 **Secure API** - JWT + Session-based authentication
- 🚀 **GitOps Deployment** - K3d + ArgoCD for continuous deployment
- 📊 **Monitoring** - Prometheus + Grafana observability stack

## 🚀 Quick Start

### **One-Command Deployment** ⭐

```bash
python3 deploy.py
```

The script will:
- ✅ Check prerequisites (Docker, kubectl, k3d)
- ✅ Create K3d cluster
- ✅ Install ArgoCD (as pods in the cluster)
- ✅ Deploy your application
- ✅ Set up GitOps continuous deployment

**That's it!** Your application will be running at:
- **Application**: http://localhost:8889
- **ArgoCD UI**: https://localhost:8080 (after port-forward)

### **What Gets Deployed**

```
K3d Cluster
├── ArgoCD Namespace
│   ├── argocd-server (UI)
│   ├── argocd-repo-server (Git sync)
│   ├── argocd-application-controller
│   └── argocd-redis
│
└── Budget-App Namespace
    ├── flask-app (your application)
    ├── nginx (reverse proxy)
    ├── postgres (database)
    ├── prometheus (monitoring)
    └── grafana (dashboards)
```

📚 **For detailed deployment instructions:**
- [Deployment Guide](DEPLOYMENT.md) - Docker Compose & K3d setup
- [Deployment Workflow](docs/DEPLOYMENT_WORKFLOW.md) - CI/CD workflow and best practices
- [Kubernetes Architecture](docs/KUBERNETES_ARCHITECTURE.md) - Complete K8s component breakdown
- [Monitoring Guide](docs/MONITORING.md) - Prometheus & Grafana setup

---

## 🎯 Deployment Architecture

This project uses **Kubernetes (K3d) with GitOps** for production-grade deployment:

| Component | Description | Access |
|-----------|-------------|--------|
| ☸️ **K3d Cluster** | Local Kubernetes cluster | Background |
| 🔄 **ArgoCD** | GitOps controller (runs as pods) | https://localhost:8080 |
| 🌐 **Application** | Budget App + PostgreSQL + Nginx | http://localhost:8889 |
| 📊 **Monitoring** | Prometheus + Grafana | Built-in |

### 🚀 Deployment Workflow

```
Run deploy.py
     ↓
K3d Cluster Created
     ↓
ArgoCD Installed (as pods)
     ↓
Application Deployed
     ↓
GitOps Ready! 🎉
```

💡 **One command deployment!** ArgoCD runs as pods inside your K3d cluster.

---

## 📋 Prerequisites

### Core Requirements
- **Docker** - Container runtime
- **kubectl** - Kubernetes CLI
- **k3d** - Local Kubernetes cluster
- **Python 3.11+** - For deployment script

### Installed Automatically by deploy.py
- **ArgoCD** - GitOps controller (installed as pods in cluster)

**Installation:**

<details>
<summary>📦 macOS</summary>

```bash
# Install via Homebrew
brew install docker kubectl k3d

# Or download Docker Desktop
# https://www.docker.com/products/docker-desktop
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

# For k3d without package manager:
# Download from: https://github.com/k3d-io/k3d/releases
```
</details>

**Verify Installation:**
```bash
docker --version
kubectl version --client
k3d version
```

---

## �� Configuration

### 1. Google OAuth Setup (Optional)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set the application type to "Web application"
6. Add authorized redirect URI:
   - `http://localhost:8889/auth/google/callback`
7. Copy the Client ID and Client Secret

### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=postgresql+psycopg2://app:securepassword123@db:5432/app
POSTGRES_DB=app
POSTGRES_USER=app
POSTGRES_PASSWORD=securepassword123

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development

# Google OAuth Configuration (optional - app works without it)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

> 💡 **Note**: The app works perfectly in **Demo Mode** without Google OAuth!

---

## 📱 Usage

### Authentication

1. **Demo Mode** (No login required):
   - Click "Skip Login (Demo Mode)"
   - Instant access with pre-loaded demo data

2. **Google OAuth**:
   - Click "Continue with Google"
   - Sign in with your Google account

### Features

- ✅ **Add Income** - Track salary and other income
- ✅ **Add Expenses** - Record spending with categories
- ✅ **Add Bills** - Track recurring bills
- ✅ **View History** - See all transactions with filtering
- ✅ **Charts** - Visual breakdown of expenses by category
- ✅ **Export CSV** - Download transaction history

---

## 🏗️ Project Structure

```
devops-final-project/
├── .github/workflows/           # CI/CD pipelines
│   └── ci-cd-gitops.yml        # GitOps CI/CD workflow
├── argocd/
│   ├── application.yaml         # ArgoCD app definition
│   └── argocd-install.yml      # ArgoCD installation reference
├── app/
│   ├── __init__.py
│   └── main.py                 # Flask application
├── k8s/                        # Kubernetes manifests
│   ├── namespace.yml
│   ├── postgres/          # PostgreSQL
│   ├── flask-app/         # Flask app
│   ├── nginx/             # Nginx reverse proxy
│   └── monitoring/        # Prometheus & Grafana
├── docs/
│   ├── GITOPS_ARGOCD.md            # GitOps + ArgoCD setup
│   ├── DEPLOYMENT_WORKFLOW.md      # Deployment workflow
│   ├── KUBERNETES_ARCHITECTURE.md  # K8s components breakdown
│   └── MONITORING.md               # Monitoring guide
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── monitoring/            # Monitoring config
├── deploy.py             # Deployment script
├── docker-compose.yml    # Docker Compose config
├── Dockerfile
├── requirements.txt
├── DEPLOYMENT.md         # Deployment guide
└── README.md
```

---

## 🗄️ Database Schema

- **families** - Family groups for budget sharing
  - `id`, `name`, `admin_user_id`, `created_at`
  
- **users** - User accounts with OAuth support
  - `id`, `email`, `password_hash`, `google_id`, `name`, `picture`, `family_id`
  
- **categories** - Expense categories
  - `id`, `name`, `family_id`, `created_at`
  
- **transactions** - Budget transactions
  - `id`, `amount`, `description`, `transaction_type`, `category_id`, `family_id`, `user_id`, `occurred_at`

---

## 🔒 Security Features

- ✅ JWT tokens for API authentication
- ✅ Google OAuth 2.0 integration
- ✅ Session-based demo mode
- ✅ Hybrid authentication system
- ✅ Family-scoped data access
- ✅ Secure password hashing
- ✅ Kubernetes secrets management
- ✅ Docker secrets via environment variables
- ✅ Trivy security scanning in CI/CD (critical vulnerabilities only)

---

## 🔄 CI/CD Pipeline - GitOps

The project uses **GitOps methodology** with ArgoCD for continuous deployment:

### Continuous Integration (CI)
- 🧪 **Build & Test** - Lint and test code on every push
- 🐳 **Docker Build** - Build and tag images with commit SHA
- 🔍 **Security Scan** - Trivy vulnerability scanning (critical only)
- 📦 **Push to GHCR** - GitHub Container Registry (private)

### Continuous Deployment (CD) - GitOps
- 🔄 **Pull-Based** - ArgoCD pulls updates from Git (secure)
- 🎯 **Automated Sync** - Detects changes every 3 minutes
- 🛡️ **Self-Healing** - Automatically fixes manual changes
- 📊 **Drift Detection** - Monitors cluster vs Git state
- 🔙 **Easy Rollback** - One-click rollback to any version
- 🎨 **Rich UI** - Visual representation of all resources

### 🚀 Automatic Setup

ArgoCD is **automatically installed** when you run `deploy.py`:

```bash
python3 deploy.py
```

**What happens:**
1. K3d cluster is created
2. ArgoCD is installed as pods in the cluster
3. Your application is deployed via GitOps
4. You're ready to go!

**Access ArgoCD UI:**
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Open https://localhost:8080
# Username: admin
# Password: (shown after deployment)
```

**Manual setup details:** See [`docs/GITOPS_ARGOCD.md`](docs/GITOPS_ARGOCD.md) for complete guide.

---

## 🧪 Testing

```bash
# Run unit tests (coming soon)
pytest tests/

# Check logs
docker-compose logs -f web

# Kubernetes logs
kubectl logs -f deployment/flask-app -n budget-app
```

---

## 🛠️ Development

### Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask app
python app/main.py
```

### Hot Reload with Docker

```bash
# Mount local directory for development
docker-compose up
# Code changes will auto-reload
```

---

## 📊 Monitoring & Observability

Integrated Prometheus + Grafana monitoring stack:

**Local (Docker Compose):**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

**Kubernetes (K3d/GKE):**
```bash
# Deploy monitoring stack
kubectl apply -f k8s/monitoring/

# Access Grafana
kubectl port-forward -n budget-app svc/grafana-service 3000:3000
```

**Metrics collected:**
- 📈 HTTP request rates
- ⚡ Response times (P50, P95, P99)
- ❌ Error rates by endpoint
- 💾 Resource usage (CPU, memory)
- 🐍 Python runtime metrics

📚 See [MONITORING.md](docs/MONITORING.md) for setup and dashboard creation

---

## 🐛 Troubleshooting

### Port Conflicts
```bash
# The deployment script handles this automatically!
# Or manually:
docker-compose down
pkill -f "kubectl.*port-forward"
```

### Docker Not Running
```bash
# macOS
open -a Docker

# Wait for Docker to start, then retry
```

### Database Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d
```

### View Logs
```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl get pods -n budget-app
kubectl logs -f deployment/flask-app -n budget-app
```

---

## 📚 Documentation

- 📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Setup guide (Docker Compose & K3d)
- 🔄 **[GITOPS_ARGOCD.md](docs/GITOPS_ARGOCD.md)** - GitOps with ArgoCD (complete guide)
- 🏗️ **[KUBERNETES_ARCHITECTURE.md](docs/KUBERNETES_ARCHITECTURE.md)** - Complete K8s architecture breakdown
- 📈 **[MONITORING.md](docs/MONITORING.md)** - Monitoring setup and dashboards
- 📝 **API Documentation** - See inline comments in `app/main.py`

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🎓 Learning Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Basics](https://kubernetes.io/docs/tutorials/kubernetes-basics/)
- [K3d Documentation](https://k3d.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)

---

## 👨‍💻 Author

**Chen Bracha**

---

## 🌟 Show Your Support

Give a ⭐️ if this project helped you learn DevOps!

---

**Made with ❤️ for learning DevOps and Kubernetes**