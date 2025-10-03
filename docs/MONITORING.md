# 📊 Monitoring Guide

## 🎯 Overview

Your Budget App now includes a complete monitoring stack with **Prometheus** and **Grafana**!

## 🌐 Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Grafana Dashboard** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | No auth |
| **Flask Metrics** | http://localhost:8887/metrics | No auth |
| **Budget App** | http://localhost:8887 | Demo mode or OAuth |

## ✨ What's Being Monitored

### Automatic Metrics (No code changes needed!)
- ✅ **HTTP Requests per second**
- ✅ **Response times** (P50, P95, P99)
- ✅ **Error rates** (4xx, 5xx)
- ✅ **Request/Response sizes**
- ✅ **Concurrent requests**

### Endpoints Tracked
- `/budget` - Main app
- `/api/budget/summary` - Balance summary
- `/api/budget/transaction` - Add transactions
- `/api/budget/transactions` - View history
- `/api/user-info` - User details
- All other endpoints automatically tracked!

## 🚀 Quick Start

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Generate Some Traffic
Visit your app and use it:
```bash
open http://localhost:8887
```

### 3. View Metrics in Grafana
```bash
open http://localhost:3000
```

Login: `admin` / `admin`

## 📈 Create Your First Dashboard

### Method 1: Import Pre-built Dashboard (Easiest!)

1. Open Grafana → http://localhost:3000
2. Login (`admin` / `admin`)
3. Go to **Dashboards** → **Import**
4. Enter Dashboard ID: **3662**
5. Select **Prometheus** datasource
6. Click **Import**

**Boom!** 💥 You have a beautiful dashboard!

### Method 2: Create Custom Dashboard

1. Open Grafana
2. Click **+** → **Dashboard** → **Add visualization**
3. Select **Prometheus** datasource
4. Use these queries:

#### Request Rate
```promql
rate(flask_http_request_total[5m])
```

#### Average Response Time
```promql
rate(flask_http_request_duration_seconds_sum[5m]) / 
rate(flask_http_request_duration_seconds_count[5m])
```

#### Error Rate
```promql
rate(flask_http_request_total{status=~"5.."}[5m])
```

#### 95th Percentile Response Time
```promql
histogram_quantile(0.95, 
  rate(flask_http_request_duration_seconds_bucket[5m]))
```

#### Top 5 Slowest Endpoints
```promql
topk(5, 
  rate(flask_http_request_duration_seconds_sum[5m]) by (path))
```

## 📸 Screenshot Ideas for Your Project

1. **Grafana Dashboard** - Show request rate, response time
2. **Prometheus Targets** - Show healthy scraping status
3. **Raw Metrics** - Show `/metrics` endpoint
4. **During Load Test** - Run `ab` or `hey` to generate traffic

## 🧪 Test Your Monitoring

### Generate Load
```bash
# Install apache-bench
brew install httpd

# Generate 1000 requests
ab -n 1000 -c 10 http://localhost:8887/
```

Watch the metrics spike in Grafana! 📈

## 🎨 Dashboard Panel Ideas

### 1. Request Overview
- Total requests counter
- Requests per second graph
- Success rate percentage

### 2. Performance
- Average response time
- P95/P99 latency
- Slow endpoints table

### 3. Errors
- Error rate graph
- Error count by status code
- Failed endpoints

### 4. Traffic
- Requests by endpoint
- Peak times
- Geographic distribution (if using cloud)

## 📊 Example Dashboard Layout

```
┌──────────────────────────────────────────────────────┐
│ 📊 BUDGET APP - PRODUCTION MONITORING              │
├──────────────────────────────────────────────────────┤
│                                                      │
│  🌐 Total Requests    ⚡ Avg Response    ❌ Errors  │
│     1,234 (+5%)          120ms (-10%)       0.5%    │
│                                                      │
│  ┌────────────────────┐  ┌───────────────────────┐ │
│  │ Request Rate (5m) │  │ Response Time P95     │ │
│  │      ╱╲            │  │   ___╱╲___           │ │
│  │     ╱  ╲___        │  │  ╱        ╲___       │ │
│  └────────────────────┘  └───────────────────────┘ │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ Top 5 Endpoints                                │ │
│  │ /api/budget/transaction ████████ 45%           │ │
│  │ /budget                 ██████ 30%             │ │
│  │ /api/budget/summary     ████ 20%               │ │
│  └────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## 🔧 Troubleshooting

### Prometheus Not Scraping
```bash
# Check Prometheus targets
open http://localhost:9090/targets

# Should show:
# flask-app (web:5000) - UP ✅
```

### No Data in Grafana
1. Check Prometheus is scraping: http://localhost:9090/targets
2. Verify datasource in Grafana (Configuration → Data Sources)
3. Test connection (should show green checkmark)
4. Generate traffic to your app first!

### View Raw Metrics
```bash
curl http://localhost:8887/metrics

# You'll see:
# flask_http_request_total{...} 123
# flask_http_request_duration_seconds_sum{...} 12.34
# ...
```

## 📚 Learning Resources

- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Pre-built Dashboards](https://grafana.com/grafana/dashboards/)
- [Flask Prometheus Exporter](https://github.com/rycus86/prometheus_flask_exporter)

## 🎓 For Your Presentation

### Key Points to Mention:
1. ✅ "Implemented production-grade monitoring with Prometheus & Grafana"
2. ✅ "Automatic metric collection from Flask application"
3. ✅ "Real-time dashboards showing request rates, latency, and errors"
4. ✅ "Uses industry-standard tools (same as Google, Netflix, etc.)"

### Demo Flow:
1. Show Grafana dashboard
2. Make a transaction in the app
3. Show metrics update in real-time
4. Highlight key metrics (response time, error rate)

## 🌟 Next Level (Optional)

Want to go further? Add:
- 📧 Email alerts when errors spike
- 📱 Slack notifications
- 🔔 PagerDuty integration
- 📊 Custom business metrics (transactions per day, etc.)

---

**Made with ❤️ for learning DevOps monitoring!** 