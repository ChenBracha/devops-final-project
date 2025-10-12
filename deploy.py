#!/usr/bin/env python3
"""
Budget App Deployment Script with GitOps (ArgoCD)
Deploys to K3d cluster with ArgoCD for continuous deployment
"""

import os
import sys
import subprocess
import time
import shutil
from pathlib import Path

def print_banner():
    """Print a nice banner for the deployment script"""
    print("=" * 70)
    print("🚀 BUDGET APP - K3D + ARGOCD DEPLOYMENT")
    print("=" * 70)
    print("This script will:")
    print("  1. Create a K3d cluster")
    print("  2. Install ArgoCD (GitOps controller)")
    print("  3. Deploy your application")
    print("=" * 70)
    print()

def check_docker():
    """Check if Docker is running"""
    if not shutil.which('docker'):
        print("❌ Docker is not installed!")
        print("\n📦 Please install Docker:")
        print("   macOS:   brew install docker")
        print("   Linux:   curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh")
        print("   Windows: choco install docker-desktop")
        return False
    
    result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ Docker is running")
        return True
    
    print("❌ Docker is not running!")
    print("📝 Please start Docker Desktop and try again")
    return False

def check_requirements():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    requirements = {
        'kubectl': 'Kubernetes CLI',
        'k3d': 'K3d (local Kubernetes)'
    }
    
    missing = []
    for tool, description in requirements.items():
        if not shutil.which(tool):
            missing.append((tool, description))
        else:
            print(f"✅ {tool} found")
    
    if missing:
        print("\n❌ Missing requirements:")
        for tool, description in missing:
            print(f"   - {tool}: {description}")
        
        print("\n📦 Installation commands:")
        print("   macOS:   brew install kubectl k3d")
        print("   Linux:   See README.md for installation instructions")
        print("   Windows: choco install kubectl k3d")
        return False
    
    return True

def run_command(command, description="Running command", check=True, capture=False):
    """Run a shell command with error handling"""
    print(f"📋 {description}...")
    
    try:
        if capture:
            result = subprocess.run(command, shell=True, check=check, 
                                  capture_output=True, text=True)
            return result
        else:
            subprocess.run(command, shell=True, check=check)
            print("✅ Success!")
            return None
    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Error: Command failed")
            if capture and e.stderr:
                print(f"   {e.stderr}")
        return None

def setup_k3d_cluster():
    """Create or start K3d cluster"""
    print("\n🏗️  STEP 1: K3D CLUSTER SETUP")
    print("-" * 70)
    
    # Check if cluster exists
    result = subprocess.run(['k3d', 'cluster', 'list'], 
                          capture_output=True, text=True)
    
    if 'budget-cluster' in result.stdout:
        print("✅ K3d cluster 'budget-cluster' exists")
        
        # Start cluster if stopped
        print("🔄 Ensuring cluster is running...")
        subprocess.run(['k3d', 'cluster', 'start', 'budget-cluster'], 
                      capture_output=True)
        time.sleep(2)
        
        # Verify kubectl can connect
        kubectl_check = subprocess.run(['kubectl', 'cluster-info'], 
                                     capture_output=True, text=True, timeout=5)
        if kubectl_check.returncode == 0:
            print("✅ Cluster is running and accessible")
            return True
        else:
            print("❌ Cluster exists but not accessible")
            return False
    else:
        print("🏗️  Creating new K3d cluster...")
        if not run_command("k3d cluster create budget-cluster --port '8889:80@loadbalancer'", 
                          "Creating K3d cluster"):
            return False
        
        print("⏳ Waiting for cluster to be ready...")
        time.sleep(5)
        
        print("✅ K3d cluster created successfully")
        return True

def install_argocd():
    """Install ArgoCD in the cluster"""
    print("\n🔄 STEP 2: ARGOCD INSTALLATION (GitOps Controller)")
    print("-" * 70)
    
    # Check if ArgoCD namespace exists
    result = subprocess.run(['kubectl', 'get', 'namespace', 'argocd'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ ArgoCD namespace already exists")
        
        # Check if ArgoCD pods are running
        pods_result = subprocess.run(['kubectl', 'get', 'pods', '-n', 'argocd'], 
                                    capture_output=True, text=True)
        
        if 'Running' in pods_result.stdout:
            print("✅ ArgoCD is already installed and running")
            return True
        else:
            print("⚠️  ArgoCD namespace exists but pods not running, reinstalling...")
    
    # Create namespace
    print("📦 Creating ArgoCD namespace...")
    run_command("kubectl create namespace argocd", "Creating namespace", check=False)
    
    # Install ArgoCD
    print("📥 Installing ArgoCD (this takes 2-3 minutes)...")
    argocd_url = "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"
    
    if not run_command(f"kubectl apply -n argocd -f {argocd_url}", 
                      "Applying ArgoCD manifests"):
        return False
    
    # Wait for ArgoCD to be ready
    print("⏳ Waiting for ArgoCD pods to be ready (may take 2-3 minutes)...")
    print("   This installs several components: server, repo-server, controller, etc.")
    
    max_wait = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        result = subprocess.run(['kubectl', 'wait', '--for=condition=Ready', 
                               'pods', '--all', '-n', 'argocd', 
                               '--timeout=30s'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ ArgoCD installed successfully!")
            
            # Show ArgoCD pods
            print("\n📊 ArgoCD components running:")
            subprocess.run(['kubectl', 'get', 'pods', '-n', 'argocd'])
            return True
        
        elapsed = int(time.time() - start_time)
        print(f"   Still waiting... ({elapsed}s)")
        time.sleep(10)
    
    print("⚠️  ArgoCD installation is taking longer than expected")
    print("   You can check status with: kubectl get pods -n argocd")
    
    # Continue anyway - might be ready soon
    return True

def get_argocd_password():
    """Retrieve ArgoCD admin password"""
    try:
        result = subprocess.run([
            'kubectl', '-n', 'argocd', 'get', 'secret', 
            'argocd-initial-admin-secret', 
            '-o', 'jsonpath={.data.password}'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            import base64
            password = base64.b64decode(result.stdout).decode('utf-8')
            return password
        else:
            return None
    except Exception:
        return None

def deploy_application():
    """Deploy the application using ArgoCD"""
    print("\n🚀 STEP 3: APPLICATION DEPLOYMENT")
    print("-" * 70)
    
    # Check if application exists
    result = subprocess.run(['kubectl', 'get', 'application', 'budget-app', '-n', 'argocd'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ ArgoCD application already exists")
        print("🔄 Syncing application...")
        
        # Trigger sync
        subprocess.run(['kubectl', 'patch', 'application', 'budget-app', 
                       '-n', 'argocd', '--type', 'merge',
                       '-p', '{"operation":{"initiatedBy":{"username":"deploy-script"},"sync":{}}}'],
                      capture_output=True)
        
        print("✅ Sync triggered")
    else:
        print("📝 Creating ArgoCD application...")
        
        if not os.path.exists('argocd/application.yaml'):
            print("❌ argocd/application.yaml not found!")
            print("   Please ensure the file exists in your repository")
            return False
        
        if not run_command("kubectl apply -f argocd/application.yaml", 
                          "Creating ArgoCD application"):
            return False
        
        print("✅ Application created")
    
    # Wait for application to sync
    print("⏳ Waiting for application to sync...")
    time.sleep(5)
    
    # Check application status
    for i in range(12):  # Wait up to 60 seconds
        result = subprocess.run([
            'kubectl', 'get', 'application', 'budget-app', 
            '-n', 'argocd', '-o', 'jsonpath={.status.sync.status}'
        ], capture_output=True, text=True)
        
        if 'Synced' in result.stdout:
            print("✅ Application synced successfully!")
            break
        
        print(f"   Syncing... ({(i+1)*5}s)")
        time.sleep(5)
    else:
        print("⚠️  Application sync is taking longer than expected")
        print("   Check ArgoCD UI for details")
    
    # Wait for pods to be ready
    print("⏳ Waiting for application pods to be ready...")
    time.sleep(10)
    
    for i in range(24):  # Wait up to 2 minutes
        result = subprocess.run(['kubectl', 'get', 'pods', '-n', 'budget-app'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0 and 'Running' in result.stdout:
            lines = result.stdout.split('\n')
            running_count = sum(1 for line in lines if 'Running' in line)
            
            if running_count >= 3:  # Wait for at least 3 pods
                print(f"✅ Application pods are running!")
                print("\n📊 Current pods:")
                subprocess.run(['kubectl', 'get', 'pods', '-n', 'budget-app'])
                return True
        
        print(f"   Waiting for pods... ({(i+1)*5}s)")
        time.sleep(5)
    
    print("⚠️  Some pods might still be starting")
    print("   Check status with: kubectl get pods -n budget-app")
    return True

def setup_access():
    """Set up access to ArgoCD and the application"""
    print("\n🌐 STEP 4: ACCESS SETUP")
    print("-" * 70)
    
    # Get ArgoCD password
    print("🔐 Retrieving ArgoCD credentials...")
    password = get_argocd_password()
    
    # Port-forward instructions
    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    
    print("\n📊 ACCESS YOUR SERVICES:")
    print()
    print("1️⃣  ArgoCD UI (GitOps Dashboard):")
    print("   Run: kubectl port-forward svc/argocd-server -n argocd 8080:443")
    print("   Open: https://localhost:8080")
    print("   Username: admin")
    if password:
        print(f"   Password: {password}")
    else:
        print("   Password: <run command to get it>")
        print("   Get password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d")
    print()
    print("2️⃣  Budget Application:")
    print("   Already accessible at: http://localhost:8889")
    print("   (K3d loadbalancer is active)")
    print()
    
    print("🔍 USEFUL COMMANDS:")
    print("   • Check application status: kubectl get application -n argocd")
    print("   • Check pods: kubectl get pods -n budget-app")
    print("   • View logs: kubectl logs -f deployment/flask-app -n budget-app")
    print("   • ArgoCD CLI: argocd app list (requires ArgoCD CLI)")
    print()
    
    print("📚 GITOPS WORKFLOW:")
    print("   1. Push code to Git")
    print("   2. GitHub Actions builds & pushes image to GHCR")
    print("   3. Update k8s manifests with new image tag")
    print("   4. ArgoCD auto-syncs (every 3 min) or click 'Sync' in UI")
    print("   5. New version deployed!")
    print()
    
    print("🛑 TO CLEANUP:")
    print("   k3d cluster delete budget-cluster")
    print()
    print("=" * 70)

def main():
    """Main deployment script"""
    print_banner()
    
    # Check if in correct directory
    if not os.path.exists('k8s'):
        print("❌ Error: k8s directory not found!")
        print("📁 Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check Docker
    print("🔍 Checking Docker...")
    if not check_docker():
        sys.exit(1)
    
    print()
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    print()
    
    try:
        # Setup K3d cluster
        if not setup_k3d_cluster():
            print("❌ Failed to setup K3d cluster")
            sys.exit(1)
        
        # Install ArgoCD
        if not install_argocd():
            print("❌ Failed to install ArgoCD")
            sys.exit(1)
        
        # Deploy application
        if not deploy_application():
            print("❌ Failed to deploy application")
            sys.exit(1)
        
        # Setup access
        setup_access()
        
        print("🎉 SUCCESS! Your GitOps-enabled Budget App is ready!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Deployment cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
