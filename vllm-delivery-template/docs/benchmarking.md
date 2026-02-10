# Benchmarking Guide

This guide covers running and interpreting load tests for vLLM servers using the benchmark module.

## Quick Start (5 Minutes)

Run your first benchmark:

```bash
# 1. Start the vLLM server
./scripts/dev.sh

# 2. In another terminal, run the benchmark
./scripts/run_benchmark.sh
```

That's it! The benchmark will:
- Test with default settings (10 concurrent requests, 100 total)
- Generate JSON and Markdown reports in `benchmark/reports/`
- Print summary statistics to the console

## Configuration

Benchmark parameters are configured via YAML file (`benchmark/config/default.yaml`):

```yaml
server:
  base_url: "http://localhost:8000/v1"
  model: "Qwen/Qwen2.5-3B-Instruct"

load:
  concurrency: 10          # Concurrent requests
  num_requests: 100        # Total requests
  warmup_requests: 10      # Warmup before test

prompt:
  input_length: 512        # Target input tokens
  output_length: 128       # Max output tokens
```

### Key Parameters

| Parameter | Description | Default | Recommendation |
|-----------|-------------|---------|----------------|
| `concurrency` | Number of simultaneous requests | 10 | Start low, increase gradually |
| `num_requests` | Total requests to send | 100 | 100-500 for good statistics |
| `warmup_requests` | Pre-test warmup requests | 10 | 5-10% of num_requests |
| `input_length` | Target input token count | 512 | Match your use case |
| `output_length` | Max output tokens | 128 | Match your use case |

## Running Benchmarks

### Basic Usage

```bash
# Use default config
python benchmark/load_test.py

# Specify config file
python benchmark/load_test.py --config benchmark/config/default.yaml

# Override parameters via CLI
python benchmark/load_test.py --concurrency 20 --num-requests 500
```

### Using the Helper Script

The `run_benchmark.sh` script provides additional features:

```bash
# Run with health checks
./scripts/run_benchmark.sh

# Run multiple times for variance testing
./scripts/run_benchmark.sh --repeat 3

# Override parameters
./scripts/run_benchmark.sh --concurrency 50 --num-requests 1000

# Skip monitoring stack check
./scripts/run_benchmark.sh --no-monitoring
```

### Reproducibility Testing

To verify results are reproducible (variance < 10%):

```bash
# Run 3 times with same config
./scripts/run_benchmark.sh --repeat 3
```

The coefficient of variation (CV) should be < 10% for throughput.

## Interpreting Reports

### Console Output

```
=== Load Test Complete ===
Duration: 45.23s
Throughput: 2.21 req/s
Successful: 100/100
Failed: 0/100

=== Statistics ===
Latency (ms):  avg=234.5  p50=220.1  p95=450.3  p99=620.7
TTFT (ms):    avg=125.3  p50=120.5  p95=180.2  p99=250.1
Tokens/sec:   145.6
```

### Key Metrics

| Metric | Description | What to Look For |
|--------|-------------|------------------|
| **Throughput** | Requests per second | Higher is better |
| **TTFT** | Time to First Token | Lower is better (user-perceived latency) |
| **P95 Latency** | 95th percentile latency | Most users experience this or better |
| **P99 Latency** | 99th percentile latency | Worst-case latency |
| **Tokens/sec** | Output generation speed | Higher is better |

### JSON Report

```json
{
  "metadata": {
    "timestamp": "2026-02-10T12:00:00",
    "config": {...}
  },
  "summary": {
    "duration_seconds": 45.23,
    "throughput_rps": 2.21,
    "successful_requests": 100
  },
  "latency": {
    "avg_ms": 234.5,
    "p95_ms": 450.3,
    "p99_ms": 620.7
  },
  "ttft": {
    "avg_ms": 125.3,
    "p95_ms": 180.2
  }
}
```

### Markdown Report

Human-readable report with tables and reproduction commands.

## Best Practices

### 1. Start Small

Begin with low concurrency and increase gradually:

```bash
# Start
./scripts/run_benchmark.sh --concurrency 5 --num-requests 50

# Scale up
./scripts/run_benchmark.sh --concurrency 10 --num-requests 100
./scripts/run_benchmark.sh --concurrency 20 --num-requests 200
```

### 2. Use Warmup

Always include warmup requests to let the model reach stable state:

```yaml
load:
  warmup_requests: 10  # 5-10% of total requests
```

### 3. Match Your Use Case

Configure prompt lengths to match your actual workload:

```yaml
prompt:
  input_length: 512   # Short: 128, Medium: 512, Long: 2048+
  output_length: 128  # Short: 64, Medium: 128, Long: 512+
```

### 4. Verify Reproducibility

Run multiple times and check variance:

```bash
./scripts/run_benchmark.sh --repeat 3
```

Coefficient of variation (CV) should be < 10% for throughput.

### 5. Compare with Monitoring

Correlate benchmark results with Grafana dashboards:

- `vllm:num_requests_total` - Request rate
- `vllm:time_to_first_token_seconds` - TTFT
- `vllm:gpu_cache_usage_perc` - GPU utilization

## Troubleshooting

### Server Not Responding

```
Error: Config file not found
```

**Solution**: Start the vLLM server first:
```bash
./scripts/dev.sh
# or
python serving/launch.py
```

### High Failure Rate

```
Failed: 15/100
```

**Possible causes**:
- Server overloaded → Reduce concurrency
- Request timeout → Increase `request_timeout` in config
- GPU memory error → Check GPU utilization

### High Variance

If throughput varies > 10% between runs:

1. **Ensure stable system**: Close other GPU processes
2. **Increase warmup**: More warmup requests
3. **Longer tests**: More total requests
4. **Check background**: No other processes consuming GPU/CPU

### Prometheus Metrics Missing

If Prometheus metrics don't appear in reports:

```bash
# Check Prometheus is running
curl http://localhost:9090/-/healthy

# Start monitoring stack
./scripts/start_monitoring.sh
```

## Advanced Usage

### Custom Prompts

Create a custom config for specific testing:

```yaml
# benchmark/config/long_context.yaml
prompt:
  prompt_type: "fixed"
  fixed_prompt: "Summarize the following article in detail..."
  input_length: 2048
  output_length: 512
```

### Rate Limited Testing

Test constant request rate:

```yaml
load:
  concurrency: 50          # Max concurrent
  request_rate: 10         # 10 req/s constant
```

### Multiple Configurations

Compare different settings:

```bash
./scripts/run_benchmark.sh --config benchmark/config/default.yaml
./scripts/run_benchmark.sh --config benchmark/config/high_concurrency.yaml
```

## Integration with Monitoring

Benchmark results correlate with Grafana panels:

| Benchmark Metric | Grafana Panel |
|------------------|---------------|
| Throughput (req/s) | `rate(vllm:num_requests_total[1m])` |
| TTFT | `vllm:time_to_first_token_seconds` |
| Latency | `vllm:time_per_request_seconds` |
| GPU Usage | `vllm:gpu_cache_usage_perc` |

Access Grafana at: http://localhost:3000 (default)

## References

- [vLLM Metrics Documentation](https://docs.vllm.ai/en/stable/design/metrics/)
- [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](http://localhost:3000)
