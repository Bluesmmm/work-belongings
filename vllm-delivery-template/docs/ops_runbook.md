# Operations Runbook

Deployment, monitoring, and maintenance guide for vLLM servers.

## System Requirements

### Minimum (Development)
- CPU: 4 cores
- RAM: 16GB
- GPU: NVIDIA RTX 3060 (12GB VRAM)
- Storage: 50GB SSD

### Recommended (Production)
- CPU: 16+ cores
- RAM: 64GB+
- GPU: NVIDIA A100 (40GB+) or multiple GPUs
- Storage: 200GB+ NVMe SSD

## Deployment

### Option 1: Systemd Service (Linux)

Create `/etc/systemd/system/vllm.service`:

```ini
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
User=vllm
WorkingDirectory=/opt/vllm-delivery-template
Environment="PATH=/opt/vllm-delivery-template/.venv/bin"
ExecStart=/opt/vllm-delivery-template/.venv/bin/python serving/launch.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable vllm
sudo systemctl start vllm
sudo systemctl status vllm
```

### Option 2: Screen/Tmux Session

```bash
# Start screen session
screen -S vllm

# Activate venv and start server
source .venv/bin/activate
python serving/launch.py

# Detach: Ctrl+A, D
# Reattach: screen -r vllm
```

## Health Checks

### HTTP Health Endpoint

```bash
curl http://localhost:8000/health
```

### Using Health Check Script

```bash
# Check if server is healthy
curl http://localhost:8000/health

# Get model info
curl http://localhost:8000/v1/models
```

## Logging

### Server Logs

```bash
# Systemd
sudo journalctl -u vllm -f

# Docker
docker logs -f vllm-server

# Direct
python serving/launch.py > logs/vllm.log 2>&1
```

### Log Rotation

Create `/etc/logrotate.d/vllm`:

```
/path/to/vllm-delivery-template/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
}
```

## Monitoring with Prometheus + Grafana

### Quick Start

```bash
# Start monitoring stack (from project root)
docker compose -f observability/docker-compose.yml up -d

# Access Grafana
# URL: http://localhost:3000
# Credentials: admin / admin
```

### Key Metrics

| Metric | Prometheus Query | Meaning |
|--------|-----------------|---------|
| **QPS** | `rate(vllm:num_requests_total[1m])` | Requests per second |
| **P95 Latency** | `histogram_quantile(0.95, rate(vllm:time_per_request_seconds_bucket[1m]))` | 95% of requests complete faster |
| **TTFT** | `histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[1m]))` | Time to first token |
| **Queue Size** | `vllm:waiting_queue_size` | Requests waiting in queue |
| **GPU Memory** | `vllm:gpu_cache_usage_perc` | KV cache memory usage |
| **Concurrent** | `vllm:num_requests_running` | Currently processing requests |

### Health Status Assessment

Use this table to quickly assess system health:

| Status | Queue | GPU Memory | P95 Latency | Action |
|--------|-------|------------|-------------|--------|
| **Healthy** | < 10 | < 80% | < 500ms | Monitor |
| **Congested** | 10-50 | 80-95% | 500ms-2s | Plan scale |
| **Critical** | > 50 | > 95% | > 2s | Scale now |

### Common Scenarios

#### High Queue, Normal GPU Memory
**Diagnosis**: CPU bottleneck or `max_num_seqs` too low

**Solution**:
```yaml
# Increase concurrent processing
max_num_seqs: 256
```

#### High GPU Memory, Normal Queue
**Diagnosis**: Memory leak or models too large

**Solution**:
```yaml
# Reduce context window
max_model_len: 4096

# Or enable CPU offloading
swap_space: 4
```

#### High Latency, Low Queue
**Diagnosis**: Batch size too small or model loading

**Solution**:
```yaml
# Increase batch size
max_num_batched_tokens: 16384
```

### Prometheus Queries for Troubleshooting

```promql
# Find preemption rate (indicates memory pressure)
rate(vllm:num_preemption[5m])

# Check error rate
rate(vllm:num_requests_finished[5m]) - rate(vllm:num_requests_success[5m])

# Average tokens per second
rate(vllm:num_generation_tokens[5m]) / rate(vllm:num_requests_finished[5m])

# KV cache blocks available
vllm:num_gpu_blocks - vllm:num_used_gpu_blocks
```

For complete monitoring setup, see [Observability README](../observability/README.md).

### Prometheus Direct Access

```bash
# Query metrics directly
curl 'http://localhost:9090/api/v1/query?query=vllm:waiting_queue_size'

# Check target status
curl http://localhost:9090/api/v1/targets
```

## Performance Tuning

### Throughput Optimization

```yaml
# serving/config.yaml
gpu_memory_utilization: 0.95
max_num_batched_tokens: 16384
max_num_seqs: 512
```

### Latency Optimization

```yaml
# serving/config.yaml
gpu_memory_utilization: 0.8
max_num_batched_tokens: 4096
max_num_seqs: 128
```

### Memory Optimization

```yaml
# serving/config.yaml
gpu_memory_utilization: 0.7
max_model_len: 4096
swap_space: 4  # Offload to CPU
```

## Troubleshooting

### High Memory Usage

```bash
# Monitor GPU memory
watch -n 1 nvidia-smi

# Reduce batch size
max_num_seqs: 64

# Enable CPU offloading
swap_space: 8
```

### Slow Inference

```bash
# Check GPU utilization
nvidia-smi dmon -s u

# Increase batch size
max_num_batched_tokens: 16384

# Use tensor parallelism
tensor_parallel_size: 2
```

### Connection Refused

```bash
# Check if server is running
curl http://localhost:8000/health

# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Check logs
sudo journalctl -u vllm -n 100
```

## Backup and Recovery

### Model Backup

```bash
# Cache HuggingFace models
export HF_HOME=/data/models
python serving/launch.py

# Backup model cache
tar -czf models-backup.tar.gz /data/models
```

### Configuration Backup

```bash
# Backup configs
cp -r serving/ serving.backup/
tar -czf configs-$(date +%Y%m%d).tar.gz serving/
```

## Security Checklist

- [ ] Change default API key
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up authentication
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Network isolation (VPC)
- [ ] Rate limiting

## Scaling

### Horizontal Scaling

Run multiple instances behind a load balancer:

```bash
# Instance 1
python serving/launch.py --port 8001

# Instance 2
python serving/launch.py --port 8002

# Use nginx/HAProxy for load balancing
```

### Vertical Scaling

Upgrade to larger GPU or use tensor parallelism:

```yaml
tensor_parallel_size: 4  # Use 4 GPUs
```
