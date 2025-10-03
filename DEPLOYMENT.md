# 🚀 Deployment Guide

This project supports **two deployment methods** that can run **simultaneously** on different ports!

## 📋 Quick Start

Run the deployment script:
```bash
python3 deploy.py
# or
./deploy.sh
```

## 🎯 Deployment Options

### 1. 🐳 Docker Compose (Port 8887)
- **Best for**: Local development, quick testing
- **URL**: http://localhost:8887
- **Setup time**: ~2 minutes
- **Requirements**: Docker, Docker Compose

**Features:**
- Simple single-command deployment
- Easy to start/stop
- Perfect for development

### 2. ☸️  Kubernetes with K3d (Port 8889)
- **Best for**: Learning Kubernetes, production-like setup
- **URL**: http://localhost:8889
- **Setup time**: ~5 minutes
- **Requirements**: Docker, kubectl, k3d

**Features:**
- Production-like environment
- Kubernetes manifest practice
- Scalable architecture
- Separate namespaces and secrets

## 💡 Running Both Simultaneously

**Yes, you can run both at the same time!** They use different ports:
- Docker Compose: `localhost:8887`
- Kubernetes: `localhost:8889`

This is useful for:
- Comparing performance
- Testing different configurations
- Learning differences between Docker Compose and Kubernetes

## 🔄 Switching Between Deployments

The deployment script automatically:
1. ✅ Detects which services are running
2. ✅ Asks if you want to stop them
3. ✅ Handles port conflicts gracefully
4. ✅ Starts Docker Desktop if needed (macOS)

### Example Flow:

```bash
$ python3 deploy.py

🔍 Checking Docker Desktop...
✅ Docker is running

Choose your deployment method:
1. 🐳 Docker Compose → http://localhost:8887
2. ☸️  Kubernetes → http://localhost:8889

💡 TIP: You can run both simultaneously on different ports!

👉 Choose deployment method (1 or 2):
```

## 🛠️ Manual Deployment

### Docker Compose
```bash
docker-compose up -d
# Access at http://localhost:8887
```

### Kubernetes
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

## 🛑 Stopping Services

### Docker Compose
```bash
docker-compose down
```

### Kubernetes
```bash
# Stop port-forward
pkill -f "kubectl.*port-forward"

# Delete cluster (optional)
k3d cluster delete budget-cluster
```

## 📊 Port Summary

| Deployment       | Port | URL                        |
|------------------|------|----------------------------|
| Docker Compose   | 8887 | http://localhost:8887      |
| Kubernetes (K3d) | 8889 | http://localhost:8889      |

## 🔍 Troubleshooting

### Port Already in Use
The script will detect this and offer to stop the existing service.

### Docker Not Running
The script will offer to start Docker Desktop automatically (macOS).

### Can't Switch Deployments
Make sure to stop the current deployment first, or choose a different port.

## 📚 Learn More

- Docker Compose: Simple, file-based orchestration
- Kubernetes: Industry-standard container orchestration
- K3d: Lightweight Kubernetes in Docker (perfect for local development) 

## 📊 **What This Data Means:**

### **What You're Looking At:**
This is **Prometheus showing ALL the metrics** it's collecting from your Flask app!

---

## 🎯 **Key Metrics Explained:**

### **1. Flask App Info** ✅
```
flask_exporter_info{app="budget-app", environment="local", 
                    instance="web:5000", version="0.23.0"}
```
**Meaning:** Your Flask app is being monitored, version 0.23.0 of the exporter is working!

---

### **2. Python Process Metrics** 🐍

```
process_cpu_seconds_total - How much CPU time your app used
process_resident_memory_bytes - RAM usage
process_virtual_memory_bytes - Virtual memory
process_open_fds - Open file descriptors
```

**What this tells you:**
- ✅ Your app is running
- ✅ It's using resources (CPU, memory)
- ✅ System health is being tracked

---

### **3. Python Garbage Collection** 🗑️

```
python_gc_collections_total{generation="0"} 
python_gc_objects_collected_total
```

**What this tells you:**
- ✅ Python is cleaning up unused memory
- ✅ Your app is running smoothly (no memory leaks if this is low)

---

### **4. Scraping Metrics** 📡

```
scrape_duration_seconds - How long it takes to collect metrics
scrape_samples_scraped - How many metrics were collected
```

**What this tells you:**
- ✅ Prometheus is successfully scraping your app
- ✅ It's collecting data every 15 seconds (default)

---

## 🚨 **What's MISSING (Important!):**

I notice you **DON'T see these metrics yet:**
```
flask_http_request_total ❌
flask_http_request_duration_seconds ❌
```

### **Why?**
**You haven't used your app yet!** 

HTTP metrics only appear **AFTER** someone visits your app!

---

## ✅ **Let's Generate Real Traffic Metrics:**

Run this to create HTTP request data:

```bash
# Generate 50 requests to different endpoints
for i in {1..10}; do
  curl -s http://localhost:8887/ > /dev/null
  curl -s http://localhost:8887/api/health > /dev/null
  curl -s http://localhost:8887/budget > /dev/null
  echo "Batch $i completed"
done

echo "✅ Traffic generated! Check Prometheus now!"
```

**Then in Prometheus, search for:**
```promql
flask_http_request_total
```

You'll now see:
```
flask_http_request_total{method="GET", path="/budget", status="302"} 10
flask_http_request_total{method="GET", path="/api/health", status="200"} 10
flask_http_request_total{method="GET", path="/", status="302"} 10
```

---

## 📈 **What You SHOULD See After Using the App:**

### **Request Metrics:**
- `flask_http_request_total` - Total number of requests
- `flask_http_request_duration_seconds` - How long requests took
- Labels will show: `method`, `path`, `status`

### **Example:**
```
flask_http_request_total{
  method="POST",
  path="/api/budget/transaction",
  status="200"
} = 5
```

**Translation:** "5 successful POST requests to add transactions"

---

## 🎨 **Now Create a Grafana Dashboard:**

1. Open **Grafana**: http://localhost:3000 (admin/admin)
2. Go to **Dashboards** → **Import**
3. Enter ID: **3662**
4. Select **Prometheus** datasource
5. Click **Import**

**You'll see:**
- 📊 Request rate graph
- ⚡ Response time chart
- ❌ Error rate
- 📈 Requests by endpoint

---

## 🎓 **For Your Project Report:**

### **What to Say:**

> "I implemented Prometheus and Grafana monitoring to track:
> - **Request rates** - How many users are using the app
> - **Response times** - Application performance (P95 latency)
> - **Error rates** - System health and reliability
> - **Resource usage** - CPU, memory consumption
> 
> The metrics are automatically collected from the Flask application
> using prometheus-flask-exporter, with no manual instrumentation needed.
> This provides real-time visibility into application health and performance."

---

## ✅ **Summary - What This Data Proves:**

1. ✅ **Monitoring is working** - Prometheus is scraping metrics
2. ✅ **Flask integration works** - App is exposing `/metrics` endpoint  
3. ✅ **System metrics available** - CPU, memory, Python stats
4. ⏳ **Need traffic** - HTTP metrics appear after app usage

---

## 🚀 **Ready to Commit?**

Your monitoring is **FULLY FUNCTIONAL**! You now have:
- ✅ Prometheus collecting metrics
- ✅ Grafana for visualization
- ✅ Automatic Flask instrumentation
- ✅ Production-grade observability

**Want to commit this and move on to the next task (Terraform for GCP)?** 🎯 