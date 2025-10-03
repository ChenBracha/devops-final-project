#!/usr/bin/env python3
"""
Budget App Deployment Script
Choose between Docker Compose or Kubernetes deployment
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def print_banner():
    """Print a nice banner for the deployment script"""
    print("=" * 60)
    print("🚀 BUDGET APP DEPLOYMENT SCRIPT")
    print("=" * 60)
    print("Choose your deployment method:")
    print()

def check_docker_desktop():
    """Check if Docker Desktop is running and offer to start it"""
    # Check if docker command exists
    if not shutil.which('docker'):
        print("❌ Docker is not installed!")
        print("\n📦 Please install Docker Desktop:")
        print("   🔗 https://www.docker.com/products/docker-desktop")
        print("\n   For macOS: Download and install Docker Desktop from the link above")
        return False
    
    # Check if Docker daemon is running
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Docker is running")
        return True
    
    # Docker is installed but not running
    print("⚠️  Docker is installed but not running")
    print("\n📝 Docker Desktop is required for Kubernetes (K3d)")
    
    response = input("\n👉 Would you like me to start Docker Desktop? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        print("🚀 Starting Docker Desktop...")
        subprocess.run(['open', '-a', 'Docker'], capture_output=True)
        
        print("⏳ Waiting for Docker to start (this may take 30-60 seconds)...")
        
        # Wait up to 90 seconds for Docker to start
        for i in range(18):  # 18 * 5 = 90 seconds
            time.sleep(5)
            result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Docker started successfully!")
                return True
            print(f"   Still waiting... ({(i+1)*5}s)")
        
        print("❌ Docker failed to start in time")
        print("📝 Please start Docker Desktop manually and try again")
        return False
    else:
        print("\n📝 Please start Docker Desktop manually:")
        print("   1. Open Docker Desktop application")
        print("   2. Wait for it to start")
        print("   3. Run this script again")
        return False

def check_requirements():
    """Check if required tools are installed"""
    requirements = {
        'docker': 'Docker is required for both deployment methods',
        'docker-compose': 'Docker Compose is required for option 1',
        'kubectl': 'kubectl is required for Kubernetes deployment',
        'k3d': 'k3d is required for local Kubernetes'
    }
    
    missing = []
    for tool, description in requirements.items():
        try:
            # Use shutil.which for simple existence check
            if not shutil.which(tool):
                missing.append((tool, description))
        except Exception:
            missing.append((tool, description))
    
    return missing

def run_command(command, description="Running command"):
    """Run a shell command with error handling"""
    print(f"📋 {description}...")
    print(f"💻 Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=False, text=True)
        print("✅ Success!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: Command failed with exit code {e.returncode}")
        return False

def deploy_docker_compose():
    """Deploy using Docker Compose"""
    print("\n🐳 DEPLOYING WITH DOCKER COMPOSE")
    print("-" * 40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found!")
        print("📝 Please create a .env file with your configuration.")
        print("💡 You can use .env.example as a template if it exists.")
        return False
    
    # Build and start services
    commands = [
        ("docker-compose down", "Stopping any existing containers"),
        ("docker-compose build", "Building Docker images"),
        ("docker-compose up -d", "Starting services in background"),
        ("docker-compose ps", "Checking service status")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            print("❌ Docker Compose deployment failed!")
            return False
    
    print("\n🎉 DOCKER COMPOSE DEPLOYMENT COMPLETE!")
    print("🌐 Your app should be available at: http://localhost:8887")
    print("📊 To view logs: docker-compose logs -f")
    print("🛑 To stop: docker-compose down")
    return True

def deploy_kubernetes():
    """Deploy using Kubernetes (K3d)"""
    print("\n☸️  DEPLOYING WITH KUBERNETES (K3D)")
    print("-" * 40)
    
    # Stop any existing services (user already confirmed)
    print("🛑 Stopping any existing services...")
    subprocess.run(['docker-compose', 'down'], capture_output=True)
    
    # Kill any kubectl port-forward processes
    try:
        subprocess.run(['pkill', '-f', 'kubectl.*port-forward'], capture_output=True)
        time.sleep(1)
    except:
        pass
    
    # Double-check Docker is still running
    docker_check = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if docker_check.returncode != 0:
        print("❌ Docker stopped running!")
        print("📝 Please ensure Docker Desktop stays running and try again.")
        return False
    
    print("✅ Docker is running")
    
    # Check if cluster exists
    result = subprocess.run(['k3d', 'cluster', 'list'], 
                          capture_output=True, text=True)
    
    if 'budget-cluster' not in result.stdout:
        print("🏗️  Creating K3d cluster...")
        if not run_command("k3d cluster create budget-cluster --port '8888:80@loadbalancer'", 
                          "Creating K3d cluster"):
            return False
    else:
        print("✅ K3d cluster 'budget-cluster' already exists")
        
        # Always try to start the cluster (in case it's stopped)
        print("🔄 Ensuring cluster is running...")
        start_result = subprocess.run(['k3d', 'cluster', 'start', 'budget-cluster'], 
                                     capture_output=True, text=True)
        
        if start_result.returncode == 0:
            print("✅ Cluster started successfully")
        else:
            # Cluster might already be running, check kubectl
            kubectl_check = subprocess.run(['kubectl', 'cluster-info'], 
                                         capture_output=True, text=True, timeout=5)
            if kubectl_check.returncode == 0:
                print("✅ Cluster is running")
            else:
                print("❌ Failed to start cluster")
                print(start_result.stderr)
                return False
    
    # Wait a moment for cluster to be ready
    print("⏳ Waiting for cluster to be ready...")
    time.sleep(3)
    
    # Check if deployments already exist
    check_result = subprocess.run(['kubectl', 'get', 'pods', '-n', 'budget-app'], 
                                capture_output=True, text=True)
    
    if check_result.returncode == 0 and 'Running' in check_result.stdout:
        print("✅ Kubernetes deployments already running!")
        print("📋 Current pods:")
        subprocess.run(['kubectl', 'get', 'pods', '-n', 'budget-app'])
        
        # Check if port-forward is needed
        pf_check = subprocess.run(['pgrep', '-f', 'kubectl.*port-forward'], 
                                capture_output=True, text=True)
        
        if pf_check.returncode != 0:
            print("🔄 Starting port-forward to access the application...")
            subprocess.Popen(['kubectl', 'port-forward', 'service/nginx-service', 
                            '8888:80', '-n', 'budget-app'])
            time.sleep(2)
        
        print("\n🎉 KUBERNETES DEPLOYMENT ALREADY COMPLETE!")
        print("🌐 Your app should be available at: http://localhost:8888")
        return True
    
    # Import Docker image into K3d cluster
    print("📦 Importing Flask app image into cluster...")
    import_result = subprocess.run(['k3d', 'image', 'import', 'devops-final-project-web:latest', 
                                   '-c', 'budget-cluster'], 
                                  capture_output=True, text=True)
    if import_result.returncode == 0:
        print("✅ Image imported successfully")
    else:
        print("⚠️  Image import warning (might already exist):", import_result.stderr)
    
    # Apply Kubernetes manifests
    k8s_commands = [
        ("kubectl apply -f k8s/namespace.yml", "Creating namespace"),
        ("kubectl apply -f k8s/postgres/secret.yml", "Creating secrets"),
        ("kubectl apply -f k8s/postgres/pv-pvc.yml", "Creating persistent storage"),
        ("kubectl apply -f k8s/postgres/deployment.yml", "Deploying PostgreSQL"),
        ("kubectl apply -f k8s/postgres/service.yml", "Creating PostgreSQL service"),
        ("kubectl apply -f k8s/flask-app/secret.yml", "Creating Flask secrets"),
        ("kubectl apply -f k8s/flask-app/deployment.yml", "Deploying Flask app"),
        ("kubectl apply -f k8s/flask-app/service.yml", "Creating Flask service"),
        ("kubectl apply -f k8s/nginx/configmap.yml", "Creating Nginx config"),
        ("kubectl apply -f k8s/nginx/deployment.yml", "Deploying Nginx"),
        ("kubectl apply -f k8s/nginx/service.yml", "Creating Nginx service"),
    ]
    
    for command, description in k8s_commands:
        if not run_command(command, description):
            print("❌ Kubernetes deployment failed!")
            return False
    
    # Wait for PostgreSQL to be ready
    print("⏳ Waiting for PostgreSQL to be ready...")
    for i in range(30):  # Wait up to 30 seconds
        result = subprocess.run(['kubectl', 'get', 'pods', '-n', 'budget-app', 
                               '--no-headers'], capture_output=True, text=True)
        if 'Running' in result.stdout:
            print("✅ PostgreSQL is ready!")
            break
        print(f"⏳ Still waiting... ({i+1}/30)")
        time.sleep(1)
    else:
        print("⚠️  PostgreSQL might not be ready yet, but continuing...")
    
    # Set up port forwarding
    print("🔄 Setting up port-forward to access the application...")
    
    # Kill any existing port-forwards
    try:
        subprocess.run(['pkill', '-f', 'kubectl.*port-forward'], capture_output=True)
    except:
        pass
    
    # Start port-forward in background (using port 8889 for Kubernetes)
    port_forward = subprocess.Popen(['kubectl', 'port-forward', 'service/nginx-service', 
                                     '8889:80', '-n', 'budget-app'],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
    
    print("✅ Port-forward started")
    time.sleep(2)
    
    # Test the connection
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8889))
        sock.close()
        
        if result == 0:
            print("✅ Application is accessible!")
        else:
            print("⚠️  Application might still be starting...")
    except:
        pass
    
    print("\n🎉 KUBERNETES DEPLOYMENT COMPLETE!")
    print("🌐 Your app is available at: http://localhost:8889")
    print("📋 Check status: kubectl get pods -n budget-app")
    print("📊 View logs: kubectl logs -f deployment/flask-app -n budget-app")
    print("🛑 To stop port-forward: pkill -f 'kubectl.*port-forward'")
    print("🛑 To cleanup cluster: k3d cluster delete budget-cluster")
    return True

def check_ports(deployment_type):
    """Check ports for the selected deployment type"""
    try:
        import socket
        
        if deployment_type == 'docker':
            port = 8887
            port_name = "Docker Compose (8887)"
        else:  # kubernetes
            port = 8889
            port_name = "Kubernetes (8889)"
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  ATTENTION: Port {port} is already in use!")
            print(f"🔍 This is likely {port_name} already running")
            print()
            print("You can:")
            print(f"  1. Stop the existing service and redeploy")
            print(f"  2. Keep it running (cancel deployment)")
            print()
            
            while True:
                choice = input("❓ Stop existing service and redeploy? (y/N): ").strip().lower()
                if choice in ['y', 'yes']:
                    print("✅ Will stop existing service and continue...")
                    # Stop services based on deployment type
                    if deployment_type == 'docker':
                        subprocess.run(['docker-compose', 'down'], capture_output=True)
                        # Also kill any port-forward that might be on 8888
                        subprocess.run(['pkill', '-f', 'kubectl.*port-forward'], capture_output=True)
                    else:
                        subprocess.run(['pkill', '-f', 'kubectl.*port-forward'], capture_output=True)
                    
                    # Force kill any process on the port
                    time.sleep(1)
                    result = subprocess.run(['lsof', f'-ti:{port}'], capture_output=True, text=True)
                    if result.stdout.strip():
                        pids = result.stdout.strip().split('\n')
                        for pid in pids:
                            subprocess.run(['kill', '-9', pid], capture_output=True)
                        print(f"✅ Killed processes on port {port}")
                    
                    time.sleep(2)
                    return True
                elif choice in ['n', 'no', '']:
                    print("👋 Deployment cancelled. The existing app will keep running.")
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no.")
        
        return True  # Port is free, continue
    except Exception as e:
        print(f"⚠️  Could not check port: {e}")
        return True  # Continue anyway

def main():
    """Main deployment script"""
    print_banner()
    
    # Check current directory
    if not os.path.exists('docker-compose.yml'):
        print("❌ Error: docker-compose.yml not found!")
        print("📁 Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check Docker Desktop first
    print("🔍 Checking Docker Desktop...")
    if not check_docker_desktop():
        sys.exit(1)
    
    print()
    print("1. 🐳 Docker Compose (Simple, local development)")
    print("   - Quick setup")
    print("   - Uses Docker Compose")
    print("   - Available at http://localhost:8887")
    print()
    print("2. ☸️  Kubernetes (K3d cluster, production-like)")
    print("   - More complex setup")
    print("   - Uses K3d + Kubernetes")
    print("   - Learn Kubernetes concepts")
    print("   - Available at http://localhost:8889")
    print()
    print("💡 TIP: You can run both simultaneously on different ports!")
    print()
    
    while True:
        try:
            choice = input("👉 Choose deployment method (1 or 2): ").strip()
            
            if choice == '1':
                print("\n🐳 You chose Docker Compose!")
                
                # Check port first
                if not check_ports('docker'):
                    sys.exit(0)
                
                # Check Docker requirements
                missing = [tool for tool, desc in check_requirements() 
                          if tool in ['docker', 'docker-compose']]
                if missing:
                    print(f"❌ Missing requirements: {', '.join(missing)}")
                    print("📦 Please install the missing tools and try again.")
                    sys.exit(1)
                
                success = deploy_docker_compose()
                break
                
            elif choice == '2':
                print("\n☸️  You chose Kubernetes!")
                
                # Check port first
                if not check_ports('kubernetes'):
                    sys.exit(0)
                
                # Check Kubernetes requirements
                missing = [tool for tool, desc in check_requirements() 
                          if tool in ['docker', 'kubectl', 'k3d']]
                if missing:
                    print(f"❌ Missing requirements: {', '.join(missing)}")
                    print("📦 Please install the missing tools and try again.")
                    print("💡 Install k3d: https://k3d.io/v5.7.4/#installation")
                    sys.exit(1)
                
                success = deploy_kubernetes()
                break
                
            else:
                print("❌ Invalid choice! Please enter 1 or 2.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Deployment cancelled by user.")
            sys.exit(0)
    
    if success:
        print(f"\n🎉 Deployment successful!")
        print("🚀 Your Budget App is ready to use!")
    else:
        print(f"\n❌ Deployment failed!")
        print("🔍 Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 