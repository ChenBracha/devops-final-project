# 🏗️ Kubernetes (K3d) Architecture Diagram

## 📊 Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    🌐 EXTERNAL WORLD                                     │
│                                   (User's Browser)                                       │
│                                  http://localhost:8889                                   │
└────────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                  🖥️  K3D CLUSTER                                         │
│                             (Local Kubernetes Environment)                               │
│                                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐   │
│  │                           📦 Namespace: budget-app                               │   │
│  │                      (Isolated environment for all resources)                    │   │
│  │                                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                    🌍 NGINX (LoadBalancer Entry Point)                   │   │   │
│  │  ├─────────────────────────────────────────────────────────────────────────┤   │   │
│  │  │  📄 K8s Resources:                                                       │   │   │
│  │  │    • nginx-service (LoadBalancer) - Port 80 → localhost:8889           │   │   │
│  │  │    • nginx deployment (1 replica)                                       │   │   │
│  │  │    • nginx-config (ConfigMap)                                           │   │   │
│  │  │                                                                          │   │   │
│  │  │  🐳 Container:                                                           │   │   │
│  │  │    • Image: nginx:stable-alpine                                         │   │   │
│  │  │    • Port: 80                                                            │   │   │
│  │  │    • Resources: 64Mi-128Mi RAM, 100m-200m CPU                           │   │   │
│  │  │                                                                          │   │   │
│  │  │  ⚙️  Configuration (from ConfigMap):                                     │   │   │
│  │  │    • Reverse proxy to flask-service:5000                                │   │   │
│  │  │    • Security headers (X-Frame-Options, X-XSS-Protection)               │   │   │
│  │  │    • Health check endpoint: /nginx-health                               │   │   │
│  │  │    • Request timeouts: 60s                                              │   │   │
│  │  │                                                                          │   │   │
│  │  │  🏥 Health Checks:                                                       │   │   │
│  │  │    • Readiness: GET /nginx-health (every 5s)                            │   │   │
│  │  │    • Liveness: GET /nginx-health (every 10s)                            │   │   │
│  │  └────────────────────────────┬────────────────────────────────────────────┘   │   │
│  │                                │ Proxies HTTP requests                          │   │
│  │                                ▼                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                   🐍 FLASK APPLICATION (Backend API)                     │   │   │
│  │  ├─────────────────────────────────────────────────────────────────────────┤   │   │
│  │  │  📄 K8s Resources:                                                       │   │   │
│  │  │    • flask-service (ClusterIP) - Internal port 5000                     │   │   │
│  │  │    • flask-app deployment (2 replicas for HA)                           │   │   │
│  │  │    • flask-secret (Secret with env vars)                                │   │   │
│  │  │                                                                          │   │   │
│  │  │  🐳 Container:                                                           │   │   │
│  │  │    • Image: devops-final-project-web:latest (local)                     │   │   │
│  │  │    • ImagePullPolicy: Never (uses local Docker image)                   │   │   │
│  │  │    • Port: 5000                                                          │   │   │
│  │  │    • Resources: 256Mi-512Mi RAM, 250m-500m CPU                          │   │   │
│  │  │                                                                          │   │   │
│  │  │  🔐 Environment Variables (from flask-secret):                          │   │   │
│  │  │    • DATABASE_URL (postgres connection string)                          │   │   │
│  │  │    • SECRET_KEY (JWT signing key)                                       │   │   │
│  │  │    • FLASK_ENV (production/development)                                 │   │   │
│  │  │    • GOOGLE_CLIENT_ID (OAuth config)                                    │   │   │
│  │  │    • GOOGLE_CLIENT_SECRET (OAuth config)                                │   │   │
│  │  │                                                                          │   │   │
│  │  │  🚀 Init Container (runs before main app):                              │   │   │
│  │  │    • wait-for-postgres: Checks postgres-service:5432 availability       │   │   │
│  │  │    • Uses pg_isready to verify DB is ready                              │   │   │
│  │  │    • Loops every 2s until DB responds                                   │   │   │
│  │  │                                                                          │   │   │
│  │  │  🏥 Health Checks:                                                       │   │   │
│  │  │    • Readiness: GET /api/health (every 5s, starts after 10s)           │   │   │
│  │  │    • Liveness: GET /api/health (every 10s, starts after 30s)           │   │   │
│  │  │                                                                          │   │   │
│  │  │  📊 Exposed via Prometheus:                                             │   │   │
│  │  │    • Python metrics, HTTP request metrics, custom app metrics           │   │   │
│  │  └──────────────────┬────────────────────────────┬───────────────────────────┘   │   │
│  │                     │ Queries Database           │ Scraped by Prometheus         │   │
│  │                     ▼                            ▼                               │   │
│  │  ┌──────────────────────────────────┐  ┌────────────────────────────────────┐  │   │
│  │  │  💾 POSTGRESQL DATABASE          │  │  📊 PROMETHEUS (Metrics)            │  │   │
│  │  ├──────────────────────────────────┤  ├────────────────────────────────────┤  │   │
│  │  │  📄 K8s Resources:               │  │  📄 K8s Resources:                  │  │   │
│  │  │    • postgres-service (ClusterIP│  │    • prometheus-service (ClusterIP) │  │   │
│  │  │      Internal port: 5432)        │  │      Internal port: 9090)           │  │   │
│  │  │    • postgres deployment         │  │    • prometheus deployment          │  │   │
│  │  │      (1 replica)                 │  │      (1 replica)                    │  │   │
│  │  │    • postgres-secret (creds)     │  │    • prometheus-config (ConfigMap)  │  │   │
│  │  │    • postgres-pv (PersistentVol) │  │    • prometheus ServiceAccount      │  │   │
│  │  │    • postgres-pvc (PVC claim)    │  │    • ClusterRole & ClusterRoleBind  │  │   │
│  │  │                                  │  │                                     │  │   │
│  │  │  🐳 Container:                   │  │  🐳 Container:                      │  │   │
│  │  │    • Image: postgres:15-alpine   │  │    • Image: prom/prometheus:latest  │  │   │
│  │  │    • Port: 5432                  │  │    • Port: 9090                     │  │   │
│  │  │    • Resources: 256Mi-512Mi RAM  │  │    • Resources: 256Mi-512Mi RAM     │  │   │
│  │  │      250m-500m CPU               │  │      250m-500m CPU                  │  │   │
│  │  │                                  │  │                                     │  │   │
│  │  │  🔐 Credentials (from secret):   │  │  ⚙️  Configuration:                 │  │   │
│  │  │    • POSTGRES_DB (database name) │  │    • Scrape interval: 15s           │  │   │
│  │  │    • POSTGRES_USER (username)    │  │    • Scrapes Flask app metrics      │  │   │
│  │  │    • POSTGRES_PASSWORD           │  │    • Service discovery via K8s API  │  │   │
│  │  │                                  │  │    • Stores metrics in /prometheus  │  │   │
│  │  │  💾 Persistent Storage:          │  │                                     │  │   │
│  │  │    • PV: 2Gi on host /tmp/...    │  │  🔐 RBAC Permissions:               │  │   │
│  │  │    • PVC: Claims 2Gi storage     │  │    • Read pods, services, endpoints │  │   │
│  │  │    • Mount: /var/lib/postgresql  │  │    • Watch for changes              │  │   │
│  │  │    • Retains data on pod restart │  │    • Discover scrape targets        │  │   │
│  │  │                                  │  │                                     │  │   │
│  │  │  🏥 Health Checks:               │  │  🏥 Health Checks:                  │  │   │
│  │  │    • Readiness: pg_isready (5s)  │  │    • Readiness: GET /-/ready (5s)   │  │   │
│  │  │    • Liveness: pg_isready (10s)  │  │    • Liveness: GET /-/healthy (10s) │  │   │
│  │  └──────────────────────────────────┘  └─────────────┬──────────────────────┘  │   │
│  │                                                       │ Data source              │   │
│  │                                                       ▼                          │   │
│  │                                    ┌────────────────────────────────────────┐   │   │
│  │                                    │  📈 GRAFANA (Visualization)             │   │   │
│  │                                    ├────────────────────────────────────────┤   │   │
│  │                                    │  📄 K8s Resources:                      │   │   │
│  │                                    │    • grafana-service (ClusterIP)        │   │   │
│  │                                    │      Internal port: 3000                │   │   │
│  │                                    │    • grafana deployment (1 replica)     │   │   │
│  │                                    │    • grafana-datasources (ConfigMap)    │   │   │
│  │                                    │    • grafana-dashboards (ConfigMap)     │   │   │
│  │                                    │                                         │   │   │
│  │                                    │  🐳 Container:                          │   │   │
│  │                                    │    • Image: grafana/grafana:latest      │   │   │
│  │                                    │    • Port: 3000                         │   │   │
│  │                                    │    • Resources: 128Mi-256Mi RAM         │   │   │
│  │                                    │      100m-200m CPU                      │   │   │
│  │                                    │                                         │   │   │
│  │                                    │  🔐 Default Credentials:                │   │   │
│  │                                    │    • Username: admin                    │   │   │
│  │                                    │    • Password: admin                    │   │   │
│  │                                    │                                         │   │   │
│  │                                    │  ⚙️  Auto-configured:                   │   │   │
│  │                                    │    • Prometheus datasource              │   │   │
│  │                                    │    • Pre-loaded dashboards              │   │   │
│  │                                    │    • Provisioning via ConfigMaps        │   │   │
│  │                                    │                                         │   │   │
│  │                                    │  🏥 Health Checks:                      │   │   │
│  │                                    │    • Readiness: GET /api/health (5s)    │   │   │
│  │                                    │    • Liveness: GET /api/health (10s)    │   │   │
│  │                                    └────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 File-by-File Breakdown

### 1️⃣ **Namespace** (`k8s/namespace.yml`)
```yaml
Purpose: Creates isolated environment "budget-app"
Why: Separates this app from other K8s resources
Resources: 1 Namespace
```

---

### 2️⃣ **PostgreSQL** (Database Layer)

#### 📄 `k8s/postgres/deployment.yml`
```yaml
What it does:
  • Creates 1 PostgreSQL pod (single replica for dev)
  • Uses postgres:15-alpine image
  • Mounts persistent storage at /var/lib/postgresql/data
  • Loads credentials from postgres-secret
  
Resource limits:
  • Memory: 256Mi (request) → 512Mi (limit)
  • CPU: 250m (request) → 500m (limit)
  
Health checks:
  • Runs pg_isready every 5s (readiness)
  • Runs pg_isready every 10s (liveness)
```

#### 📄 `k8s/postgres/service.yml`
```yaml
What it does:
  • Creates internal service "postgres-service"
  • Type: ClusterIP (only accessible within cluster)
  • Exposes port 5432
  • Routes traffic to postgres pods
```

#### 📄 `k8s/postgres/secret.yml`
```yaml
What it does:
  • Stores sensitive database credentials
  • Contains: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
  • Values are base64 encoded
  • Injected as environment variables into postgres container
```

#### 📄 `k8s/postgres/pv-pvc.yml`
```yaml
What it does:
  • PersistentVolume: Defines 2Gi storage on host at /tmp/k3d-postgres-data
  • PersistentVolumeClaim: Requests 2Gi storage for postgres
  • Why: Data persists even if postgres pod restarts
  • ReclaimPolicy: Retain (data not deleted when PVC is deleted)
```

---

### 3️⃣ **Flask Application** (Backend API)

#### 📄 `k8s/flask-app/deployment.yml`
```yaml
What it does:
  • Creates 2 Flask pods (replicas for high availability)
  • Uses local Docker image: devops-final-project-web:latest
  • ImagePullPolicy: Never (must build locally first)
  
Init Container:
  • wait-for-postgres: Waits for DB to be ready before starting app
  • Uses pg_isready to check postgres-service:5432
  
Environment:
  • All secrets from flask-secret (DATABASE_URL, SECRET_KEY, etc.)
  
Resource limits:
  • Memory: 256Mi → 512Mi
  • CPU: 250m → 500m
  
Health checks:
  • Readiness: GET /api/health every 5s
  • Liveness: GET /api/health every 10s
```

#### 📄 `k8s/flask-app/service.yml`
```yaml
What it does:
  • Creates internal service "flask-service"
  • Type: ClusterIP (only accessible within cluster)
  • Exposes port 5000
  • Load balances between 2 Flask replicas
```

#### 📄 `k8s/flask-app/secret.yml`
```yaml
What it does:
  • Stores Flask configuration as environment variables
  • Contains: DATABASE_URL, SECRET_KEY, FLASK_ENV, OAuth credentials
  • Injected into Flask container
  • Values are base64 encoded
```

---

### 4️⃣ **Nginx** (Reverse Proxy / Entry Point)

#### 📄 `k8s/nginx/deployment.yml`
```yaml
What it does:
  • Creates 1 Nginx pod
  • Uses nginx:stable-alpine image
  • Mounts nginx.conf from ConfigMap
  
Resource limits:
  • Memory: 64Mi → 128Mi (lightweight)
  • CPU: 100m → 200m
  
Health checks:
  • Readiness: GET /nginx-health every 5s
  • Liveness: GET /nginx-health every 10s
```

#### 📄 `k8s/nginx/service.yml`
```yaml
What it does:
  • Creates external service "nginx-service"
  • Type: LoadBalancer ⚠️ THIS IS THE ENTRY POINT
  • Exposes port 80 → maps to localhost:8889 (via k3d)
  • Routes external traffic to nginx pod
```

#### 📄 `k8s/nginx/configmap.yml`
```yaml
What it does:
  • Stores nginx.conf configuration
  • Configures reverse proxy to flask-service:5000
  • Adds security headers (X-Frame-Options, X-XSS-Protection)
  • Creates /nginx-health endpoint
  • Sets timeouts (60s for all proxy operations)
```

---

### 5️⃣ **Prometheus** (Metrics Collection)

#### 📄 `k8s/monitoring/prometheus-deployment.yml`
```yaml
What it does:
  • Creates 1 Prometheus pod
  • Uses prom/prometheus:latest image
  • Mounts config from prometheus-config ConfigMap
  
RBAC (Security):
  • ServiceAccount: prometheus
  • ClusterRole: Can read pods, services, endpoints (for service discovery)
  • ClusterRoleBinding: Links ServiceAccount to ClusterRole
  
Storage:
  • Uses emptyDir for metrics (ephemeral, lost on restart)
  • Production would use PersistentVolume
  
Configuration:
  • Scrapes Flask app metrics every 15s
  • Uses Kubernetes service discovery
  • Stores time-series data
  
Resource limits:
  • Memory: 256Mi → 512Mi
  • CPU: 250m → 500m
  
Health checks:
  • Readiness: GET /-/ready
  • Liveness: GET /-/healthy
```

#### 📄 `k8s/monitoring/prometheus-configmap.yml`
```yaml
What it does:
  • Defines prometheus.yml configuration
  • Sets scrape interval (15s)
  • Configures scrape targets:
    - flask-service:5000 (application metrics)
  • Enables service discovery in K8s
```

---

### 6️⃣ **Grafana** (Metrics Visualization)

#### 📄 `k8s/monitoring/grafana-deployment.yml`
```yaml
What it does:
  • Creates 1 Grafana pod
  • Uses grafana/grafana:latest image
  • Auto-configures Prometheus datasource
  • Auto-loads dashboards
  
Environment:
  • Admin user: admin / admin
  • Provisioning path for auto-configuration
  
Volumes:
  • grafana-storage: emptyDir (dashboards lost on restart)
  • grafana-datasources: ConfigMap with Prometheus connection
  • grafana-dashboards-provider: ConfigMap with dashboard definitions
  
Resource limits:
  • Memory: 128Mi → 256Mi
  • CPU: 100m → 200m
```

#### 📄 `k8s/monitoring/grafana-configmap.yml`
```yaml
What it does:
  • grafana-datasources: Configures Prometheus as data source
    - URL: http://prometheus-service:9090
    - Type: prometheus
    - Access: proxy (server-side queries)
  
  • grafana-dashboards: Enables dashboard auto-loading
    - Scans provisioning directory for .json files
```

---

## 🔄 Traffic Flow (Complete Journey)

### 1. User Request Flow
```
User Browser (localhost:8889)
    ↓ HTTP GET /
nginx-service (LoadBalancer, Port 80)
    ↓ Routes to
nginx Pod (Port 80)
    ↓ Reads config from nginx-config ConfigMap
    ↓ Reverse proxy to upstream: flask-service:5000
    ↓
flask-service (ClusterIP, Port 5000)
    ↓ Load balances to
Flask Pod 1 or Flask Pod 2 (Port 5000)
    ↓ Reads DATABASE_URL from flask-secret
    ↓ SQL Query
postgres-service (ClusterIP, Port 5432)
    ↓ Routes to
PostgreSQL Pod (Port 5432)
    ↓ Reads data from
Persistent Volume (2Gi at /tmp/k3d-postgres-data)
```

### 2. Metrics Collection Flow
```
Prometheus Pod
    ↓ Scrapes every 15s (configured in prometheus-config)
    ↓ HTTP GET http://flask-service:5000/metrics
Flask Pod (exposes /metrics endpoint)
    ↓ Returns metrics (requests, latency, errors, Python stats)
Prometheus Pod
    ↓ Stores in time-series DB (/prometheus volume)
    ↓
Grafana Pod queries Prometheus
    ↓ Datasource: http://prometheus-service:9090
    ↓ Renders on dashboards (configured via grafana-datasources ConfigMap)
```

### 3. Startup Flow (Pod Initialization)
```
1. Kubernetes applies namespace.yml
   → Creates "budget-app" namespace

2. Kubernetes applies postgres/
   → Creates postgres-pv (storage volume)
   → Creates postgres-pvc (claims storage)
   → Creates postgres-secret (credentials)
   → Creates postgres-service (internal DNS)
   → Creates postgres deployment
       → Postgres pod starts
       → Mounts PVC to /var/lib/postgresql/data
       → Loads secrets as env vars
       → Runs readiness probe (pg_isready)
       → Becomes ready

3. Kubernetes applies flask-app/
   → Creates flask-secret (config)
   → Creates flask-service (internal DNS)
   → Creates flask-app deployment
       → Init container "wait-for-postgres" runs
           → Loops: pg_isready -h postgres-service -p 5432
           → Waits until postgres responds
       → Main Flask container starts
           → Loads secrets as env vars
           → Connects to postgres via DATABASE_URL
           → Exposes /api/health endpoint
           → Runs readiness probe (GET /api/health)
           → Becomes ready

4. Kubernetes applies nginx/
   → Creates nginx-config ConfigMap
   → Creates nginx-service (LoadBalancer)
   → Creates nginx deployment
       → Nginx pod starts
       → Mounts ConfigMap as nginx.conf
       → Proxies to flask-service:5000
       → Exposes /nginx-health
       → Runs readiness probe
       → Becomes ready
       → LoadBalancer assigns external IP

5. Kubernetes applies monitoring/
   → Creates prometheus resources
       → ServiceAccount for RBAC
       → ClusterRole (read permissions)
       → ClusterRoleBinding
       → prometheus-config ConfigMap
       → prometheus-service
       → prometheus deployment
           → Starts scraping targets
   
   → Creates grafana resources
       → grafana-datasources ConfigMap
       → grafana-dashboards ConfigMap
       → grafana-service
       → grafana deployment
           → Auto-configures Prometheus datasource
           → Loads dashboards
```

---

## 🔐 Security Model

### 1. **Network Segmentation**
```
Internet
    ↓ ONLY entry point
nginx-service (LoadBalancer)
    ↓ Internal cluster network only
flask-service (ClusterIP) ← NOT accessible from outside
postgres-service (ClusterIP) ← NOT accessible from outside
prometheus-service (ClusterIP) ← NOT accessible from outside
grafana-service (ClusterIP) ← NOT accessible from outside
```

### 2. **Secrets Management**
```yaml
postgres-secret:
  - POSTGRES_PASSWORD (database password)
  - POSTGRES_USER (database user)
  - POSTGRES_DB (database name)

flask-secret:
  - DATABASE_URL (full connection string with password)
  - SECRET_KEY (JWT signing key)
  - GOOGLE_CLIENT_SECRET (OAuth secret)
  
All secrets:
  - Base64 encoded
  - Only accessible within namespace
  - Injected as environment variables (not in code)
```

### 3. **RBAC (Role-Based Access Control)**
```yaml
Prometheus RBAC:
  - ServiceAccount: prometheus (identity)
  - ClusterRole: Can only READ pods, services, endpoints
  - Cannot: Write, delete, or modify anything
  - Why: Needs to discover services for scraping
```

### 4. **Resource Limits**
```
Every container has:
  • requests: Minimum guaranteed resources
  • limits: Maximum allowed resources
  
Why:
  - Prevents one container from consuming all cluster resources
  - Ensures fair scheduling
  - Triggers auto-scaling in production
```

---

## 💾 Data Persistence

### PostgreSQL Data
```
Host Machine: /tmp/k3d-postgres-data
    ↓ Mapped via PersistentVolume
K8s PersistentVolume (2Gi)
    ↓ Claimed by
PersistentVolumeClaim (postgres-pvc)
    ↓ Mounted into
PostgreSQL Container: /var/lib/postgresql/data
    ↓
Database files persist even if:
  - Pod restarts
  - Deployment updates
  - Container crashes
```

### Monitoring Data (Ephemeral)
```
Prometheus: Uses emptyDir (lost on pod restart)
Grafana: Uses emptyDir (lost on pod restart)

Why ephemeral?
  - This is a development environment
  - Production would use PersistentVolumes
  - Metrics can be regenerated
```

---

## 📊 Resource Allocation

| Component  | Pods | CPU Request | CPU Limit | Memory Request | Memory Limit |
|------------|------|-------------|-----------|----------------|--------------|
| Nginx      | 1    | 100m        | 200m      | 64Mi           | 128Mi        |
| Flask      | 2    | 250m        | 500m      | 256Mi          | 512Mi        |
| PostgreSQL | 1    | 250m        | 500m      | 256Mi          | 512Mi        |
| Prometheus | 1    | 250m        | 500m      | 256Mi          | 512Mi        |
| Grafana    | 1    | 100m        | 200m      | 128Mi          | 256Mi        |
| **TOTAL**  | **6**| **1200m**   | **2400m** | **1216Mi**     | **2432Mi**   |

*Note: 1000m CPU = 1 CPU core*

---

## 🔍 Health Checks Explained

### Readiness Probe
```
Purpose: Is the container ready to receive traffic?
If fails: Pod removed from Service load balancing
If passes: Pod added to Service endpoints

Flask example:
  httpGet:
    path: /api/health      ← Must return 200 OK
    port: 5000
  initialDelaySeconds: 10  ← Wait 10s before first check
  periodSeconds: 5         ← Check every 5s
```

### Liveness Probe
```
Purpose: Is the container alive and healthy?
If fails: Kubernetes RESTARTS the container
If passes: Container continues running

PostgreSQL example:
  exec:
    command: pg_isready    ← Check if DB accepts connections
  initialDelaySeconds: 30  ← Wait 30s before first check
  periodSeconds: 10        ← Check every 10s
```

---

## 🚀 Deployment Command Breakdown

```bash
kubectl apply -f k8s/namespace.yml
# Creates the "budget-app" namespace

kubectl apply -f k8s/postgres/
# Applies ALL files in postgres/:
#   - pv-pvc.yml (storage first)
#   - secret.yml (credentials)
#   - service.yml (DNS name)
#   - deployment.yml (pods)

kubectl apply -f k8s/flask-app/
# Applies ALL files in flask-app/:
#   - secret.yml (config)
#   - service.yml (internal DNS)
#   - deployment.yml (pods with init container)

kubectl apply -f k8s/nginx/
# Applies ALL files in nginx/:
#   - configmap.yml (nginx.conf)
#   - service.yml (LoadBalancer - external access!)
#   - deployment.yml (pods)

kubectl apply -f k8s/monitoring/
# Applies ALL files in monitoring/:
#   - prometheus-configmap.yml (scrape config)
#   - prometheus-deployment.yml (metrics collection)
#   - grafana-configmap.yml (datasources + dashboards)
#   - grafana-deployment.yml (visualization)
```

---

## 🌐 Accessing Services

### From Outside Cluster (Your Browser)
```bash
http://localhost:8889
# Maps to nginx-service (LoadBalancer)
# This is the ONLY external entry point
```

### From Inside Cluster (Pod-to-Pod)
```bash
# Flask connects to Postgres:
postgres-service:5432  # or postgres-service.budget-app.svc.cluster.local

# Nginx connects to Flask:
flask-service:5000

# Grafana connects to Prometheus:
prometheus-service:9090

# Prometheus scrapes Flask:
flask-service:5000/metrics
```

---

## 🧩 ConfigMaps vs Secrets

### ConfigMap (Non-sensitive configuration)
```yaml
nginx-config:
  • nginx.conf (proxy rules, timeouts)
  • Plain text, not encrypted
  • Can be edited without rebuilding images

prometheus-config:
  • prometheus.yml (scrape configs)
  • Scrape intervals, targets

grafana-datasources:
  • Prometheus connection URL
  • Dashboard provisioning config
```

### Secret (Sensitive data)
```yaml
postgres-secret:
  • Database passwords
  • Base64 encoded (not encrypted!)
  • Should use sealed-secrets or Vault in production

flask-secret:
  • JWT signing keys
  • OAuth client secrets
  • Database connection strings with passwords
```

---

## 🎯 Key Differences vs Docker Compose

| Aspect              | Docker Compose          | Kubernetes (K3d)           |
|---------------------|-------------------------|----------------------------|
| **Orchestration**   | Single host            | Cluster (can be multi-node)|
| **High Availability**| No (1 container)       | Yes (2 Flask replicas)     |
| **Load Balancing**  | Nginx only             | K8s Services + Nginx       |
| **Health Checks**   | Healthcheck directive  | Readiness + Liveness probes|
| **Scaling**         | Manual                 | `kubectl scale`            |
| **Restarts**        | restart: always        | Automatic (liveness probes)|
| **Storage**         | Docker volumes         | PersistentVolumes/Claims   |
| **Secrets**         | .env files             | Kubernetes Secrets         |
| **Networking**      | Bridge network         | Overlay network (ClusterIP)|
| **Service Discovery**| DNS (service names)   | DNS (service.namespace.svc)|
| **Config**          | docker-compose.yml     | Multiple YAML manifests    |
| **Production Ready**| No                     | Yes                        |

---

## 📚 Questions Your DevSecOps Team Might Ask

### Q: How do we inject our company secrets?
**A:** Replace `k8s/*/secret.yml` files with your secret management:
- Use Kubernetes Secrets
- Or integrate with Vault/AWS Secrets Manager
- Or use Sealed Secrets (encrypted at rest)

### Q: How do we change resource limits for production?
**A:** Edit `resources:` sections in deployment files:
```yaml
resources:
  requests:
    memory: "1Gi"    # Increase for production
    cpu: "1000m"
  limits:
    memory: "2Gi"
    cpu: "2000m"
```

### Q: How do we monitor this in our company infrastructure?
**A:** 
- Prometheus is already configured
- Point your company Grafana at `prometheus-service:9090`
- Or export metrics to your central monitoring (Datadog, New Relic, etc.)

### Q: What about SSL/TLS?
**A:** 
- Add Ingress with cert-manager
- Or terminate SSL at company load balancer
- Nginx can be configured for SSL (add certificates as secrets)

### Q: How do we handle database migrations?
**A:**
- Add a Kubernetes Job for Alembic migrations
- Or use init container in Flask deployment
- Run before main application starts

### Q: Can this run on our company's K8s cluster?
**A:** Yes! Just change:
- `imagePullPolicy: Never` → `imagePullPolicy: Always`
- Push images to your company registry
- Update image names to point to your registry
- Configure network policies per company standards

---

**This diagram represents the LOCAL K3D deployment. Next, I can create the Docker Compose diagram if you'd like!**


