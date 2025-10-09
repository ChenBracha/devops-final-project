# K3d: Single Node vs Multi-Node Comparison

## 🎯 Visual Comparison

### Current Setup (1 Node)
```
┌──────────────────────────────────────────┐
│    k3d-budget-cluster-server-0           │
│    (Control Plane + Worker)              │
│                                          │
│  All 6 pods run here:                    │
│  • nginx (1)                             │
│  • flask-app (2 replicas)                │
│  • postgres (1)                          │
│  • prometheus (1)                        │
│  • grafana (1)                           │
│                                          │
│  💥 Single Point of Failure              │
└──────────────────────────────────────────┘
```

### Multi-Node Setup (2 Workers)
```
┌────────────────────────┐
│  k3d-server-0          │
│  (Control Plane Only)  │
│  • Schedules pods      │
│  • Manages cluster     │
└────────────────────────┘
           │
     ┌─────┴──────┐
     ↓            ↓
┌─────────────┐  ┌─────────────┐
│  agent-0    │  │  agent-1    │
│  (Worker 1) │  │  (Worker 2) │
│             │  │             │
│  • nginx    │  │  • flask-2  │
│  • flask-1  │  │  • promethe │
│  • postgres │  │  • grafana  │
└─────────────┘  └─────────────┘

🛡️ High Availability
```

---

## 🔍 How to Check Node Distribution

### Step 1: Create Multi-Node Cluster
```bash
# Delete existing cluster first
k3d cluster delete budget-cluster

# Create with 2 worker nodes
k3d cluster create budget-cluster \
  --servers 1 \
  --agents 2 \
  --port '8889:80@loadbalancer'
```

### Step 2: Check Nodes
```bash
# List all nodes
kubectl get nodes

# Output:
# NAME                          STATUS   ROLES                  AGE
# k3d-budget-cluster-server-0   Ready    control-plane,master   1m
# k3d-budget-cluster-agent-0    Ready    <none>                 1m
# k3d-budget-cluster-agent-1    Ready    <none>                 1m
```

### Step 3: Deploy Your App
```bash
# Deploy normally
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/flask-app/
kubectl apply -f k8s/nginx/
```

### Step 4: See Pod Distribution
```bash
# Check which node each pod is on
kubectl get pods -n budget-app -o wide

# Output shows NODE column:
# NAME                      READY   STATUS    NODE
# flask-app-xxx-1           1/1     Running   k3d-budget-cluster-agent-0
# flask-app-xxx-2           1/1     Running   k3d-budget-cluster-agent-1
# nginx-xxx                 1/1     Running   k3d-budget-cluster-agent-0
# postgres-xxx              1/1     Running   k3d-budget-cluster-agent-1
# prometheus-xxx            1/1     Running   k3d-budget-cluster-agent-0
# grafana-xxx               1/1     Running   k3d-budget-cluster-agent-1
```

---

## 🧪 Test 1: Node Failure Simulation

### Single Node (Current)
```bash
# Stop the only node
docker stop k3d-budget-cluster-server-0

# Check pods
kubectl get pods -n budget-app
# Error: Unable to connect to server

# Result: COMPLETE OUTAGE 💥
```

### Multi-Node
```bash
# Stop worker node 1
docker stop k3d-budget-cluster-agent-0

# Check pods (from control plane, still accessible)
kubectl get pods -n budget-app

# Output:
# NAME                      READY   STATUS        NODE
# flask-app-xxx-1           1/1     Terminating   agent-0 (down)
# flask-app-xxx-2           1/1     Running       agent-1 ✅
# nginx-xxx                 0/1     Terminating   agent-0 (down)
# postgres-xxx              1/1     Running       agent-1 ✅

# After 30 seconds, Kubernetes reschedules:
# flask-app-xxx-3           1/1     Running       agent-1 ✅
# nginx-xxx-2               1/1     Running       agent-1 ✅

# Result: PARTIAL OUTAGE, then RECOVERY 🛡️
```

### Restart the Node
```bash
docker start k3d-budget-cluster-agent-0

# Kubernetes automatically rebalances pods
```

---

## 🧪 Test 2: Pod Spreading

### Force Flask Pods to Different Nodes

Update `k8s/flask-app/deployment.yml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flask-app
spec:
  replicas: 2
  template:
    spec:
      # ADD THIS: Spread pods across nodes
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - flask-app
              topologyKey: kubernetes.io/hostname
      containers:
      - name: flask-app
        # ... rest of config
```

**What this does:**
- Tells Kubernetes: "Try to put Flask replicas on DIFFERENT nodes"
- If one node fails, at least one Flask pod survives on another node

### Test It
```bash
# Apply the change
kubectl apply -f k8s/flask-app/deployment.yml

# Verify spreading
kubectl get pods -n budget-app -o wide | grep flask-app

# Should show:
# flask-app-xxx-1    Running    agent-0
# flask-app-xxx-2    Running    agent-1  ← Different node!
```

---

## 🧪 Test 3: Resource Exhaustion

### Single Node Scenario
```bash
# Scale up Flask to 10 replicas
kubectl scale deployment flask-app --replicas=10 -n budget-app

# Check status
kubectl get pods -n budget-app

# Result:
# 3-4 pods Running ✅
# 6-7 pods Pending ⚠️ (not enough resources on single node)
```

### Multi-Node Scenario
```bash
# Same scaling
kubectl scale deployment flask-app --replicas=10 -n budget-app

# Result:
# 8-10 pods Running ✅ (spread across 2 nodes)
# More capacity available!
```

---

## 🧪 Test 4: Rolling Updates

### Single Node
```bash
# Update Flask image
kubectl set image deployment/flask-app flask-app=new-image:v2 -n budget-app

# What happens:
# 1. Old pod terminates
# 2. New pod starts
# 3. Brief downtime (both pods on same node)
```

### Multi-Node
```bash
# Same update
kubectl set image deployment/flask-app flask-app=new-image:v2 -n budget-app

# What happens:
# 1. Old pod on agent-0 terminates
# 2. New pod starts on agent-0
# 3. Old pod on agent-1 still running ✅ (zero downtime!)
# 4. Once new pod ready, old pod on agent-1 terminates
# 5. Second new pod starts

# Result: ZERO DOWNTIME 🎉
```

---

## 📊 Performance Comparison

### Network Latency

**Single Node:**
```bash
# From inside Flask pod
time curl postgres-service:5432
# ~0.1ms (localhost)
```

**Multi-Node (cross-node):**
```bash
# If Flask on agent-0, Postgres on agent-1
time curl postgres-service:5432
# ~1-2ms (Docker bridge network)

# Still very fast for local development!
```

---

## 💰 Resource Cost Comparison

### Your Laptop

**Single Node:**
```
RAM Usage: ~500MB
CPU Usage: ~5% idle
Containers: 1
Startup Time: ~10 seconds
```

**Two Nodes:**
```
RAM Usage: ~800MB-1GB
CPU Usage: ~8% idle
Containers: 3
Startup Time: ~20 seconds
```

### GCP/Production

**Single Node:**
```
Cost: ~$35/month (1x e2-small)
Risk: Single point of failure
```

**Two Nodes:**
```
Cost: ~$70/month (2x e2-small)
Benefit: High availability
```

---

## 🎓 When to Use Each

### Use Single Node (Current Setup) ✅
- **Development**: Quick iteration, testing features
- **Learning Basics**: Understanding K8s concepts
- **Resource Constrained**: Older laptop, limited RAM
- **Simple Testing**: Just need app running

### Use Multi-Node 🚀
- **Learning Advanced K8s**: Node affinity, taints, tolerations
- **Simulating Production**: Testing HA, failover
- **Before DevSecOps Review**: Show production-like setup
- **Testing Resilience**: Node failures, pod rescheduling
- **Presentations**: Impress with real distributed system

---

## 🛠️ Quick Commands

### Switch to Multi-Node
```bash
# Backup current deployment (if needed)
kubectl get all -n budget-app -o yaml > backup.yaml

# Delete single-node cluster
k3d cluster delete budget-cluster

# Create multi-node
k3d cluster create budget-cluster \
  --servers 1 \
  --agents 2 \
  --port '8889:80@loadbalancer'

# Redeploy
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/flask-app/
kubectl apply -f k8s/nginx/
kubectl apply -f k8s/monitoring/
```

### Switch Back to Single-Node
```bash
k3d cluster delete budget-cluster

# Your original command
k3d cluster create budget-cluster --port '8889:80@loadbalancer'

# Redeploy
# ... same as above
```

---

## 🎯 Recommendation for DevSecOps Presentation

**Show Both!** 

1. **Start with single-node**: "This is how I develop locally"
2. **Demo multi-node**: "This simulates production"
3. **Show node failure recovery**: "Watch Kubernetes reschedule pods"
4. **Explain GCP will have 2-3 nodes**: "Production has real HA"

This shows you understand:
- Development vs Production differences
- High availability concepts
- Kubernetes scheduling
- Resource management
- Failure recovery

---

## 📚 Key Takeaways

| Feature | Single Node | Multi-Node |
|---------|-------------|------------|
| **Setup Time** | 10 seconds | 20 seconds |
| **Resource Usage** | 500MB RAM | 1GB RAM |
| **Production-like** | ❌ No | ✅ Yes |
| **High Availability** | ❌ No | ✅ Yes |
| **Learning Value** | Basic | Advanced |
| **Failure Testing** | ❌ Can't test | ✅ Can test |
| **Best For** | Development | Testing/Demo |

---

**Bottom Line:** 
- Your **current 1-node setup is PERFECT for development** 🎯
- For your **DevSecOps presentation, consider 2-node** to show you understand production concepts 🚀
- In **GCP with Terraform, you already have 2 nodes configured** ☁️

