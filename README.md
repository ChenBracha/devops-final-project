# Israeli Budget App 💰🇮🇱

> A family budget management application with dual-deployment architecture (Docker Compose + Kubernetes)

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Supported-326CE5?logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

A family budget management application built with Flask, featuring Google OAuth authentication, demo mode, and support for both Docker Compose and Kubernetes deployments.

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
- 🚀 **Dual Deployment** - Run on Docker Compose OR Kubernetes

## 🚀 Quick Start

### **Option 1: Use the Automated Deployment Script (Recommended)** ⭐

```bash
# Python script
python3 deploy.py

# OR Bash script
./deploy.sh
```

The script will:
- ✅ Check Docker Desktop status (start it if needed)
- ✅ Let you choose Docker Compose or Kubernetes
- ✅ Handle port conflicts automatically
- ✅ Deploy everything with one command

### **Option 2: Manual Deployment**

#### Docker Compose (Port 8887)
```bash
docker-compose up -d
# Access at http://localhost:8887
```

#### Kubernetes with K3d (Port 8889)
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

📚 **For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

---

## 🎯 Deployment Architecture

This project supports **two deployment methods** that can run **simultaneously**:

| Method | Port | URL | Best For |
|--------|------|-----|----------|
| 🐳 Docker Compose | 8887 | http://localhost:8887 | Quick development, testing |
| ☸️ Kubernetes (K3d) | 8889 | http://localhost:8889 | Learning K8s, production-like setup |

💡 **You can run both at the same time!** Perfect for comparing performance or learning differences.

---

## 📋 Prerequisites

- Docker Desktop (for macOS) or Docker Engine
- Docker Compose (for traditional deployment)
- kubectl (for Kubernetes deployment)
- k3d (for local Kubernetes cluster)
- Python 3.11+ (optional, for deployment script)

---

## �� Configuration

### 1. Google OAuth Setup (Optional)

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
5. Set the application type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8887/auth/google/callback` (Docker Compose)
   - `http://localhost:8889/auth/google/callback` (Kubernetes)
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
├── app/
│   ├── __init__.py
│   └── main.py              # Flask application
├── k8s/                     # Kubernetes manifests
│   ├── namespace.yml
│   ├── postgres/           # PostgreSQL deployment
│   ├── flask-app/          # Flask app deployment
│   └── nginx/              # Nginx deployment
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf
├── monitoring/              # Prometheus/Grafana (optional)
├── deploy.py               # Python deployment script
├── deploy.sh               # Bash deployment script
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── DEPLOYMENT.md           # Detailed deployment guide
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
- ✅ Trivy security scanning in CI/CD (critical vulnerabilities only)

---

## 🔄 CI/CD Pipeline

The project includes GitHub Actions workflows:

- 🧪 **Build & Test** - Lint and test code
- 🐳 **Docker Build** - Build and scan Docker images
- 🔍 **Security Scan** - Trivy vulnerability scanning (critical only)
- 📦 **Artifact Upload** - Save build artifacts

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

## 📊 Monitoring (Optional)

Add Prometheus + Grafana monitoring:

```bash
# Add to docker-compose.yml
# See DEPLOYMENT.md for instructions
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

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

- 📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- 🏗️ **Architecture Diagram** - Coming soon
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

---

## 👨‍💻 Author

**Chen Bracha**

---

## 🌟 Show Your Support

Give a ⭐️ if this project helped you learn DevOps!

---

**Made with ❤️ for learning DevOps and Kubernetes**