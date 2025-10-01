#!/bin/bash

# Budget App Deployment Script
# Choose between Docker Compose or Kubernetes deployment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_banner() {
    echo "============================================================"
    echo "🚀 BUDGET APP DEPLOYMENT SCRIPT"
    echo "============================================================"
    echo "Choose your deployment method:"
    echo ""
}

check_docker_desktop() {
    # Check if docker command exists
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed!${NC}"
        echo ""
        echo "📦 Please install Docker Desktop:"
        echo "   🔗 https://www.docker.com/products/docker-desktop"
        echo ""
        echo "   For macOS: Download and install Docker Desktop from the link above"
        return 1
    fi
    
    # Check if Docker daemon is running
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✅ Docker is running${NC}"
        return 0
    fi
    
    # Docker is installed but not running
    echo -e "${YELLOW}⚠️  Docker is installed but not running${NC}"
    echo ""
    echo "📝 Docker Desktop is required for Kubernetes (K3d)"
    echo ""
    read -p "👉 Would you like me to start Docker Desktop? (y/n): " response
    
    if [[ "$response" =~ ^[Yy] ]]; then
        echo "🚀 Starting Docker Desktop..."
        open -a Docker
        
        echo "⏳ Waiting for Docker to start (this may take 30-60 seconds)..."
        
        # Wait up to 90 seconds for Docker to start
        for i in {1..18}; do
            sleep 5
            if docker ps &> /dev/null; then
                echo -e "${GREEN}✅ Docker started successfully!${NC}"
                return 0
            fi
            echo "   Still waiting... ($((i*5))s)"
        done
        
        echo -e "${RED}❌ Docker failed to start in time${NC}"
        echo "📝 Please start Docker Desktop manually and try again"
        return 1
    else
        echo ""
        echo "📝 Please start Docker Desktop manually:"
        echo "   1. Open Docker Desktop application"
        echo "   2. Wait for it to start"
        echo "   3. Run this script again"
        return 1
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ $1 is not installed!${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $1 is available${NC}"
        return 0
    fi
}

run_command() {
    local cmd="$1"
    local description="$2"
    
    echo -e "${BLUE}📋 $description...${NC}"
    echo -e "${CYAN}💻 Command: $cmd${NC}"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✅ Success!${NC}"
        return 0
    else
        echo -e "${RED}❌ Error: Command failed!${NC}"
        return 1
    fi
}

deploy_docker_compose() {
    echo -e "\n${BLUE}🐳 DEPLOYING WITH DOCKER COMPOSE${NC}"
    echo "----------------------------------------"
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  .env file not found!${NC}"
        echo "📝 Please create a .env file with your configuration."
        echo "💡 You can use .env.example as a template if it exists."
        return 1
    fi
    
    # Build and start services
    run_command "docker-compose down" "Stopping any existing containers" || true
    run_command "docker-compose build" "Building Docker images" || return 1
    run_command "docker-compose up -d" "Starting services in background" || return 1
    run_command "docker-compose ps" "Checking service status" || return 1
    
    echo -e "\n${GREEN}🎉 DOCKER COMPOSE DEPLOYMENT COMPLETE!${NC}"
    echo "🌐 Your app should be available at: http://localhost:8887"
    echo "📊 To view logs: docker-compose logs -f"
    echo "🛑 To stop: docker-compose down"
    return 0
}

deploy_kubernetes() {
    echo -e "\n${PURPLE}☸️  DEPLOYING WITH KUBERNETES (K3D)${NC}"
    echo "----------------------------------------"
    
    # Stop any existing services (user already confirmed)
    echo "🛑 Stopping any existing services..."
    docker-compose down 2>/dev/null || true
    
    # Kill any kubectl port-forward processes
    pkill -f "kubectl.*port-forward" 2>/dev/null || true
    sleep 2
    
    # Check Docker is running
    if ! docker ps >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running!${NC}"
        echo "📝 Please start Docker Desktop or Docker Engine first."
        return 1
    fi
    
    # Check if cluster exists
    if k3d cluster list | grep -q "budget-cluster"; then
        echo -e "${GREEN}✅ K3d cluster 'budget-cluster' already exists${NC}"
        
        # Always try to start the cluster (in case it's stopped)
        echo "🔄 Ensuring cluster is running..."
        if k3d cluster start budget-cluster 2>/dev/null; then
            echo -e "${GREEN}✅ Cluster started successfully${NC}"
        elif kubectl cluster-info >/dev/null 2>&1; then
            echo -e "${GREEN}✅ Cluster is running${NC}"
        else
            echo -e "${RED}❌ Failed to start cluster${NC}"
            return 1
        fi
    else
        echo "🏗️  Creating K3d cluster..."
        run_command "k3d cluster create budget-cluster --port '8888:80@loadbalancer'" "Creating K3d cluster" || return 1
    fi
    
    # Wait for cluster to be ready
    echo "⏳ Waiting for cluster to be ready..."
    sleep 3
    
    # Check if deployments already exist
    if kubectl get pods -n budget-app 2>/dev/null | grep -q "Running"; then
        echo -e "${GREEN}✅ Kubernetes deployments already running!${NC}"
        echo "📋 Current pods:"
        kubectl get pods -n budget-app
        
        # Check if port-forward is needed
        if ! pgrep -f "kubectl.*port-forward" >/dev/null; then
            echo "🔄 Starting port-forward to access the application..."
            kubectl port-forward service/nginx-service 8888:80 -n budget-app &
            sleep 2
        fi
        
        echo -e "\n${GREEN}🎉 KUBERNETES DEPLOYMENT ALREADY COMPLETE!${NC}"
        echo "🌐 Your app should be available at: http://localhost:8888"
        return 0
    fi
    
    # Import Docker image
    echo "📦 Importing Flask app image into cluster..."
    if k3d image import devops-final-project-web:latest -c budget-cluster 2>/dev/null; then
        echo -e "${GREEN}✅ Image imported successfully${NC}"
    else
        echo -e "${YELLOW}⚠️  Image import warning (might already exist)${NC}"
    fi
    
    # Apply Kubernetes manifests
    echo "📋 Applying Kubernetes manifests..."
    
    run_command "kubectl apply -f k8s/namespace.yml" "Creating namespace" || return 1
    run_command "kubectl apply -f k8s/postgres/secret.yml" "Creating secrets" || return 1
    run_command "kubectl apply -f k8s/postgres/pv-pvc.yml" "Creating persistent storage" || return 1
    run_command "kubectl apply -f k8s/postgres/deployment.yml" "Deploying PostgreSQL" || return 1
    run_command "kubectl apply -f k8s/postgres/service.yml" "Creating PostgreSQL service" || return 1
    run_command "kubectl apply -f k8s/flask-app/secret.yml" "Creating Flask secrets" || return 1
    run_command "kubectl apply -f k8s/flask-app/deployment.yml" "Deploying Flask app" || return 1
    run_command "kubectl apply -f k8s/flask-app/service.yml" "Creating Flask service" || return 1
    run_command "kubectl apply -f k8s/nginx/configmap.yml" "Creating Nginx config" || return 1
    run_command "kubectl apply -f k8s/nginx/deployment.yml" "Deploying Nginx" || return 1
    run_command "kubectl apply -f k8s/nginx/service.yml" "Creating Nginx service" || return 1
    
    # Wait for PostgreSQL to be ready
    echo "⏳ Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if kubectl get pods -n budget-app --no-headers | grep -q "Running"; then
            echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
            break
        fi
        echo "⏳ Still waiting... ($i/30)"
        sleep 1
    done
    
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}⚠️  PostgreSQL might not be ready yet, but continuing...${NC}"
    fi
    
    # Set up port forwarding
    echo "🔄 Setting up port-forward to access the application..."
    
    # Kill any existing port-forwards
    pkill -f "kubectl.*port-forward" 2>/dev/null || true
    
    # Start port-forward in background (using port 8889 for Kubernetes)
    kubectl port-forward service/nginx-service 8889:80 -n budget-app >/dev/null 2>&1 &
    
    echo -e "${GREEN}✅ Port-forward started${NC}"
    sleep 2
    
    # Test the connection
    if nc -z localhost 8889 2>/dev/null; then
        echo -e "${GREEN}✅ Application is accessible!${NC}"
    else
        echo -e "${YELLOW}⚠️  Application might still be starting...${NC}"
    fi
    
    echo -e "\n${GREEN}🎉 KUBERNETES DEPLOYMENT COMPLETE!${NC}"
    echo "🌐 Your app is available at: http://localhost:8889"
    echo "📋 Check status: kubectl get pods -n budget-app"
    echo "📊 View logs: kubectl logs -f deployment/flask-app -n budget-app"
    echo "🛑 To stop port-forward: pkill -f 'kubectl.*port-forward'"
    echo "🛑 To cleanup cluster: k3d cluster delete budget-cluster"
    return 0
}

check_ports() {
    local deployment_type="$1"
    local port
    local port_name
    
    if [ "$deployment_type" = "docker" ]; then
        port=8887
        port_name="Docker Compose (8887)"
    else
        port=8889
        port_name="Kubernetes (8889)"
    fi
    
    # Check if port is in use
    if nc -z localhost "$port" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  ATTENTION: Port $port is already in use!${NC}"
        echo "🔍 This is likely $port_name already running"
        echo ""
        echo "You can:"
        echo "  1. Stop the existing service and redeploy"
        echo "  2. Keep it running (cancel deployment)"
        echo ""
        
        while true; do
            read -p "❓ Stop existing service and redeploy? (y/N): " choice
            case $choice in
                [Yy]|[Yy][Ee][Ss])
                    echo "✅ Will stop existing service and continue..."
                    # Stop services based on deployment type
                    if [ "$deployment_type" = "docker" ]; then
                        docker-compose down 2>/dev/null || true
                        # Also kill any port-forward that might be on 8888
                        pkill -f "kubectl.*port-forward" 2>/dev/null || true
                    else
                        pkill -f "kubectl.*port-forward" 2>/dev/null || true
                    fi
                    
                    # Force kill any process on the port
                    sleep 1
                    local pids=$(lsof -ti:"$port" 2>/dev/null)
                    if [ -n "$pids" ]; then
                        echo "$pids" | xargs kill -9 2>/dev/null || true
                        echo -e "${GREEN}✅ Killed processes on port $port${NC}"
                    fi
                    
                    sleep 2
                    return 0
                    ;;
                [Nn]|[Nn][Oo]|"")
                    echo "👋 Deployment cancelled. The existing app will keep running."
                    return 1
                    ;;
                *)
                    echo -e "${RED}❌ Please enter 'y' for yes or 'n' for no.${NC}"
                    ;;
            esac
        done
    fi
    
    return 0  # Port is free, continue
}

main() {
    print_banner
    
    # Check current directory
    if [ ! -f "docker-compose.yml" ]; then
        echo -e "${RED}❌ Error: docker-compose.yml not found!${NC}"
        echo "📁 Please run this script from the project root directory."
        exit 1
    fi
    
    # Check port 8888 first
    # Check Docker Desktop first
    echo "🔍 Checking Docker Desktop..."
    if ! check_docker_desktop; then
        exit 1
    fi
    
    echo ""
    echo "1. 🐳 Docker Compose (Simple, local development)"
    echo "   - Quick setup"
    echo "   - Uses Docker Compose"
    echo "   - Available at http://localhost:8887"
    echo ""
    echo "2. ☸️  Kubernetes (K3d cluster, production-like)"
    echo "   - More complex setup"
    echo "   - Uses K3d + Kubernetes"
    echo "   - Learn Kubernetes concepts"
    echo "   - Available at http://localhost:8889"
    echo ""
    echo "💡 TIP: You can run both simultaneously on different ports!"
    echo ""
    
    while true; do
        read -p "👉 Choose deployment method (1 or 2): " choice
        
        case $choice in
            1)
                echo -e "\n${BLUE}🐳 You chose Docker Compose!${NC}"
                
                # Check port first
                if ! check_ports "docker"; then
                    exit 0
                fi
                
                # Check Docker requirements
                echo "🔍 Checking requirements..."
                if ! check_command "docker" || ! check_command "docker-compose"; then
                    echo -e "${RED}📦 Please install the missing tools and try again.${NC}"
                    exit 1
                fi
                
                if deploy_docker_compose; then
                    success=true
                else
                    success=false
                fi
                break
                ;;
            2)
                echo -e "\n${PURPLE}☸️  You chose Kubernetes!${NC}"
                
                # Check port first
                if ! check_ports "kubernetes"; then
                    exit 0
                fi
                
                # Check Kubernetes requirements
                echo "🔍 Checking requirements..."
                if ! check_command "docker" || ! check_command "kubectl" || ! check_command "k3d"; then
                    echo -e "${RED}📦 Please install the missing tools and try again.${NC}"
                    echo "💡 Install k3d: https://k3d.io/v5.7.4/#installation"
                    exit 1
                fi
                
                if deploy_kubernetes; then
                    success=true
                else
                    success=false
                fi
                break
                ;;
            *)
                echo -e "${RED}❌ Invalid choice! Please enter 1 or 2.${NC}"
                ;;
        esac
    done
    
    if [ "$success" = true ]; then
        echo -e "\n${GREEN}🎉 Deployment successful!${NC}"
        echo "🚀 Your Budget App is ready to use!"
    else
        echo -e "\n${RED}❌ Deployment failed!${NC}"
        echo "🔍 Please check the error messages above."
        exit 1
    fi
}

# Handle Ctrl+C gracefully
trap 'echo -e "\n\n👋 Deployment cancelled by user."; exit 0' INT

main "$@" 