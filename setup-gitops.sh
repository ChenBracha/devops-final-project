#!/bin/bash

##############################################################################
# GitOps Setup Script with ArgoCD
# This script sets up the complete GitOps infrastructure
##############################################################################

set -e  # Exit on error

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Setting up GitOps with ArgoCD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install: brew install kubectl"
    exit 1
fi

if ! command -v k3d &> /dev/null; then
    echo "❌ k3d not found. Please install: brew install k3d"
    exit 1
fi

echo "✅ Prerequisites OK"
echo ""

# Check if cluster exists
echo "🔍 Checking K3d cluster..."
if k3d cluster list | grep -q "budget-cluster"; then
    echo "✅ K3d cluster exists"
else
    echo "⚠️  K3d cluster not found. Creating..."
    k3d cluster create budget-cluster --port "8889:80@loadbalancer"
    sleep 5
fi

# Verify kubectl can connect
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to cluster"
    exit 1
fi

echo "✅ Cluster is accessible"
echo ""

# Install ArgoCD
echo "📦 Installing ArgoCD..."

if kubectl get namespace argocd &> /dev/null; then
    echo "⚠️  ArgoCD namespace already exists, skipping installation"
else
    echo "Creating ArgoCD namespace..."
    kubectl create namespace argocd
    
    echo "Installing ArgoCD (this takes 2-3 minutes)..."
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    echo "⏳ Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=Ready pods --all -n argocd --timeout=300s || {
        echo "⚠️  Some pods took longer than expected, continuing..."
    }
fi

echo "✅ ArgoCD installed"
echo ""

# Create ArgoCD application
echo "🎯 Creating ArgoCD application..."

if kubectl get application budget-app -n argocd &> /dev/null; then
    echo "⚠️  Application already exists, updating..."
    kubectl apply -f argocd/application.yaml
else
    echo "Creating application..."
    kubectl apply -f argocd/application.yaml
fi

echo "✅ Application created"
echo ""

# Get ArgoCD password
echo "🔐 Getting ArgoCD credentials..."
ARGOCD_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret \
    -o jsonpath="{.data.password}" 2>/dev/null | base64 -d)

if [ -z "$ARGOCD_PASSWORD" ]; then
    echo "⚠️  Could not retrieve password (may not be ready yet)"
    ARGOCD_PASSWORD="<run: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d>"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ GitOps Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Access ArgoCD UI:"
echo "   1. Run port-forward:"
echo "      kubectl port-forward svc/argocd-server -n argocd 8080:443"
echo ""
echo "   2. Open browser:"
echo "      https://localhost:8080"
echo ""
echo "   3. Login with:"
echo "      Username: admin"
echo "      Password: $ARGOCD_PASSWORD"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Next Steps:"
echo "   1. Make sure your GitHub package is public"
echo "   2. Push code to trigger CI/CD"
echo "   3. ArgoCD will auto-sync every 3 minutes"
echo ""
echo "🔍 Useful Commands:"
echo "   kubectl get application -n argocd"
echo "   kubectl get pods -n budget-app"
echo "   kubectl get pods -n argocd"
echo ""
echo "📖 Full guide: docs/GITOPS_ARGOCD.md"
echo ""

