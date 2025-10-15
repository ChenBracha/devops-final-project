# 📊 Monitoring Stack

This directory contains configuration for Prometheus + Grafana monitoring.

## 🎯 What Gets Monitored

### Flask App Metrics (Automatic)
- ✅ **Request Rate** - Requests per second
- ✅ **Response Time** - P50, P95, P99 latency
- ✅ **Error Rate** - 4xx/5xx errors
- ✅ **Request Size** - Incoming request sizes
- ✅ **Response Size** - Outgoing response sizes
- ✅ **Active Requests** - Concurrent requests

### System Metrics
- CPU usage
- Memory usage
- Network I/O

## 🚀 Quick Start

### Deploy with Monitoring
```bash
# Monitoring is automatically deployed
python3 deploy.py
```

### Access Dashboards

**Grafana:**
```bash
kubectl port-forward -n budget-app svc/grafana-service 3000:3000
open http://localhost:3000
# Username: admin, Password: admin
```

**Prometheus:**
```bash
kubectl port-forward -n budget-app svc/prometheus-service 9090:9090
open http://localhost:9090
```

**Flask Metrics:**
```bash
curl http://localhost:8080/metrics
```

## 📈 Using Grafana

### First Time Setup
1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Prometheus is already configured as datasource!
4. Create your first dashboard or import one

### Useful Queries

**Request Rate:**
```promql
rate(flask_http_request_total[5m])
```

**Average Response Time:**
```promql
rate(flask_http_request_duration_seconds_sum[5m]) / rate(flask_http_request_duration_seconds_count[5m])
```

**Error Rate:**
```promql
rate(flask_http_request_total{status=~"5.."}[5m])
```

**95th Percentile Response Time:**
```promql
histogram_quantile(0.95, rate(flask_http_request_duration_seconds_bucket[5m]))
```

## 🎨 Import Pre-built Dashboard

1. Go to Grafana → Dashboards → Import
2. Use Dashboard ID: `3662` (Prometheus Flask Exporter)
3. Select Prometheus datasource
4. Click Import

This gives you a beautiful pre-built dashboard!

## 📊 What You'll See

```
┌─────────────────────────────────────────────────┐
│ 📊 BUDGET APP DASHBOARD                        │
├─────────────────────────────────────────────────┤
│  🌐 Total Requests: 1,234 ▲ 5%                │
│  ⚡ Avg Response: 120ms ▼ 10%                  │
│  ❌ Error Rate: 0.5%                           │
│                                                 │
│  [Line Graph: Requests Per Second]             │
│  [Line Graph: Response Time P95]               │
│  [Bar Chart: Top Endpoints]                    │
└─────────────────────────────────────────────────┘
```

## 🛠️ Configuration Files

- `prometheus.yml` - Prometheus configuration
- `grafana/datasources/` - Grafana datasource config
- `grafana/dashboards/` - Dashboard provisioning

## 🔍 Troubleshooting

### Prometheus not scraping metrics
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Should show flask-app as UP
```

### Grafana not showing data
1. Check datasource connection (Configuration → Data Sources)
2. Verify Prometheus URL: `http://prometheus:9090`
3. Test the connection

### View raw metrics
```bash
curl http://localhost:8080/metrics
```

## 📚 Learn More

- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)
- [Flask Exporter Docs](https://github.com/rycus86/prometheus_flask_exporter) 