# Quick Start Guide

Get your vLLM server running in 30 minutes with this step-by-step guide.

## Prerequisites

- Python 3.10 or higher
- CUDA-compatible GPU (NVIDIA)
- Linux or macOS system

## Step 1: Install uv (2 minutes)

`uv` is a fast Python package manager that's 10-100x faster than pip.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv
```

## Step 2: Clone and Setup (3 minutes)

```bash
# Clone the repository
git clone <repo-url>
cd vllm-delivery-template

# Create virtual environment with uv
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate
```

## Step 3: Install Dependencies (5 minutes)

```bash
# Install all dependencies with uv (much faster than pip)
uv pip install -e .
```

This installs:
- `vllm` - The core inference engine
- `pyyaml` - Configuration file parsing
- `openai` - OpenAI-compatible client
- `pytest` - Testing framework
- `httpx` - HTTP client for health checks

## Step 4: Configure Model (2 minutes)

Edit `serving/config.yaml` to customize your model:

```yaml
model: "Qwen/Qwen2.5-3B-Instruct"  # Change this to your model
port: 8000
gpu_memory_utilization: 0.9
max_model_len: 8192
```

## Step 5: Start Server (5 minutes)

```bash
# Option A: One-click startup (recommended for development)
./scripts/dev.sh

# Option B: Manual startup
python serving/launch.py
```

You should see:
```
Starting vLLM server: vllm serve Qwen/Qwen2.5-3B-Instruct --port 8000 ...
Model: Qwen/Qwen2.5-3B-Instruct
Port: 8000
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**First run tip:** The model will be downloaded automatically. This may take a few minutes depending on your internet speed.

## Step 6: Run Smoke Test (5 minutes)

Open a new terminal and run:

```bash
# Activate venv first
source .venv/bin/activate

# Run smoke test
python client/smoke_test.py
```

Expected output:
```
Connecting to: http://localhost:8000/v1
Test 1: Listing models...
  Available models: ['Qwen/Qwen2.5-3B-Instruct']
Test 2: Simple chat completion...
  Response: OK
Test 3: Streaming completion...
  Streamed response: 1 2 3
✅ All smoke tests passed!
```

## Step 7: Use with OpenAI Client

Now you can use the server with any OpenAI-compatible client:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="token-abc123"
)

response = client.chat.completions.create(
    model="Qwen/Qwen2.5-3B-Instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100,
)

print(response.choices[0].message.content)
```

## Troubleshooting

### "command not found: uv"
Install uv first: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### "CUDA out of memory"
Lower `gpu_memory_utilization` in `serving/config.yaml`:
```yaml
gpu_memory_utilization: 0.7
```

### "Connection refused"
Make sure the server is running. Check terminal where you launched it.

### "Model not found"
The model will download automatically on first run. Check your internet connection.

## Monitoring & Observability

### Quick Start with Monitoring

Start the monitoring stack alongside your vLLM server:

```bash
# In one terminal: Start vLLM server (metrics enabled by default)
python serving/launch.py

# In another terminal: Start Prometheus + Grafana
docker compose -f observability/docker-compose.yml up -d
```

### Access Grafana Dashboard

1. Open http://localhost:3000 in your browser
2. Login with `admin` / `admin`
3. Open the **vLLM Monitoring Dashboard**

### Key Metrics at a Glance

| Metric | What It Shows | Healthy Range |
|--------|---------------|---------------|
| **QPS** | Requests per second | Matches your load |
| **Queue Size** | Requests waiting | < 10 |
| **GPU Memory** | KV cache usage | < 80% |
| **P95 Latency** | 95th percentile request time | < 500ms |
| **TTFT** | Time to first token | < 500ms |

### Verify Metrics Endpoint

```bash
curl http://localhost:8000/metrics | grep vllm
```

Expected output includes:
- `vllm:num_requests_total`
- `vllm:time_to_first_token_seconds`
- `vllm:gpu_cache_usage_perc`

For detailed monitoring setup and interpretation, see the [Observability README](../observability/README.md).

## Next Steps

- Read [Configuration Reference](configuration.md) for advanced options
- Check [Ops Runbook](ops_runbook.md) for deployment guidance
- Run `pytest tests/` for the full test suite
- Explore [Monitoring Guide](../observability/README.md) for detailed observability setup
