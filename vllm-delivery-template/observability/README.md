# vLLM Monitoring & Observability

This directory contains the monitoring stack for vLLM inference servers using Prometheus and Grafana.

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- vLLM server running with metrics enabled (default: `http://localhost:8000/metrics`)

### Start Monitoring Stack

```bash
# From project root
docker compose -f observability/docker-compose.yml up -d
```

### Access Dashboards

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |

### Verify Metrics

```bash
# Check if vLLM metrics are exposed
curl http://localhost:8000/metrics

# Expected output includes:
# vllm:num_requests_total
# vllm:time_to_first_token_seconds
# vllm:gpu_cache_usage_perc
# ...
```

## Dashboard Guide

### vLLM Monitoring Dashboard

The default dashboard includes the following panels:

#### 1. QPS (Requests per Second)
**Metric**: `rate(vllm:num_requests_total[1m])`

Shows the throughput of your inference server.

- **Healthy**: Stable QPS matching your expected load
- **Warning**: Sudden drops may indicate service issues

#### 2. Waiting Queue Size
**Metric**: `vllm:waiting_queue_size`

Number of requests waiting to be processed.

| Status | Value | Action |
|--------|-------|--------|
| Healthy | < 10 | No action needed |
| Congestion | 10-50 | Monitor closely, consider scaling |
| Critical | > 50 | Immediate action needed |

#### 3. GPU Cache Usage %
**Metric**: `vllm:gpu_cache_usage_perc`

Percentage of GPU KV cache memory used.

| Status | Value | Action |
|--------|-------|--------|
| Healthy | < 80% | Optimal |
| Warning | 80-95% | Consider reducing `max_model_len` or increasing GPU memory |
| Critical | > 95% | Near OOM, immediate action required |

#### 4. Request Latency (P50/P95/P99)
**Metric**: `histogram_quantile(..., vllm:time_per_request_seconds)`

Latency distribution for completed requests.

| Status | P95 Latency | Action |
|--------|-------------|--------|
| Excellent | < 200ms | Optimal |
| Good | 200ms-500ms | Acceptable for most use cases |
| Degraded | 500ms-2s | Investigate bottleneck |
| Poor | > 2s | Service degradation |

#### 5. Time to First Token (TTFT)
**Metric**: `histogram_quantile(..., vllm:time_to_first_token_seconds)`

Time until the first token is generated. Critical for interactive applications.

- **Target**: < 500ms for chat applications
- **Acceptable**: 500ms-1s for less interactive use cases

#### 6. Request States
**Metrics**: `vllm:num_requests_running`, `vllm:num_requests_waiting`, `vllm:num_requests_finished`

Shows concurrent requests and system state.

#### 7. GPU Memory Usage Over Time
**Metric**: `vllm:gpu_cache_usage_perc`

Historical view of GPU memory utilization.

#### 8. Server Status
**Metric**: `up{job="vllm-server"}`

Health check showing if the server is up (1) or down (0).

#### 9. Success vs Error Rate
**Metrics**: `rate(vllm:num_requests_success[1m])`, `rate(vllm:num_requests_finished) - rate(vllm:num_requests_success)`

Monitors request success and failure rates.

#### 10. Generation Throughput
**Metric**: `rate(vllm:num_generation_tokens[1m])`

Tokens generated per second, a key throughput metric.

## System Health Interpretation Guide

### 3-Minute Health Assessment

Use this quick guide to assess your vLLM server health:

| Indicator | Healthy | Congested | Near OOM |
|-----------|---------|-----------|----------|
| Queue Size | < 10 | 10-50 | > 50 |
| GPU Memory | < 80% | 80-95% | > 95% |
| P95 Latency | < 500ms | 500ms-2s | > 2s |
| TTFT P95 | < 500ms | 500ms-1s | > 1s |
| Success Rate | > 99% | 95-99% | < 95% |

### Action Matrix

| Situation | Immediate Action | Long-term Solution |
|-----------|-----------------|-------------------|
| High Queue + Normal GPU | Increase `max_num_seqs` | Add more GPUs |
| High Queue + High GPU | Reduce `max_model_len` | Upgrade GPU memory |
| High Latency + Low Queue | Check `max_num_batched_tokens` | Enable tensor parallelism |
| Low Success Rate | Check logs for errors | Add retry logic in client |
| Spiky Metrics | Enable request rate limiting | Implement load balancing |

## Architecture

```
┌─────────────────┐     /metrics      ┌──────────────┐
│   vLLM Server   │ ◄─────────────────┤              │
│  (localhost:    │   scrape every    │  Prometheus  │
│    8000)        │        15s        │  (port 9090) │
└─────────────────┘                   └──────┬───────┘
                                             │
                                             │ query
                                             ▼
                                     ┌──────────────┐
                                     │              │
                                     │   Grafana    │
                                     │  (port 3000) │
                                     │              │
                                     └──────────────┘
```

## Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Orchestrates Prometheus + Grafana containers |
| `prometheus/prometheus.yml` | Configures scrape targets and intervals |
| `grafana/provisioning/datasources/datasource.yml` | Auto-configures Prometheus datasource |
| `grafana/provisioning/dashboards/dashboard.yml` | Auto-loads dashboards |
| `grafana/dashboards/vllm-dashboard.json` | Main vLLM monitoring dashboard |

## Customization

### Adjust Scrape Interval

Edit `prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 30s  # Default is 15s
```

### Add Alert Rules

Create `prometheus/alerts.yml`:

```yaml
groups:
  - name: vllm_alerts
    rules:
      - alert: HighQueueSize
        expr: vllm:waiting_queue_size > 50
        for: 5m
        annotations:
          summary: "High queue size detected"
```

Update `docker-compose.yml` to mount alerts file.

## Troubleshooting

### No Data in Dashboard

1. **Verify vLLM is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check metrics endpoint**:
   ```bash
   curl http://localhost:8000/metrics | grep vllm
   ```

3. **Verify Prometheus scraping**:
   - Go to http://localhost:9090/targets
   - Check if `vllm-server` is "UP"

4. **Check container logs**:
   ```bash
   docker logs vllm-prometheus
   docker logs vllm-grafana
   ```

### Docker Network Issues

If Prometheus can't reach vLLM, verify `host.docker.internal` works:

```bash
docker run --rm alpine ping -c 1 host.docker.internal
```

On Linux, ensure `extra_hosts` is configured in `docker-compose.yml`.

### Reset Monitoring Stack

```bash
# Stop and remove containers
docker compose -f observability/docker-compose.yml down -v

# Restart
docker compose -f observability/docker-compose.yml up -d
```

## Stopping the Stack

```bash
docker compose -f observability/docker-compose.yml down
```

To also remove persisted data:

```bash
docker compose -f observability/docker-compose.yml down -v
```

## References

- [vLLM Metrics Documentation](https://docs.vllm.ai/en/stable/design/metrics/)
- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard JSON](https://grafana.com/docs/grafana/latest/dashboards/json-model/)
