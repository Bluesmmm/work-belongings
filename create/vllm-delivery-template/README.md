# vLLM Delivery Template

A production-ready template for serving Large Language Models using vLLM with OpenAI-compatible API.

## Quick Start

> 30-minute "start → call → return" flow

```bash
# 1. Clone and setup environment (uses uv for fast package management)
git clone <repo-url>
cd vllm-delivery-template
uv venv
source .venv/bin/activate

# 2. Install dependencies
uv pip install -e .

# 3. Start the vLLM server
python serving/launch.py

# 4. Run smoke test (in another terminal)
python client/smoke_test.py
```

## Project Structure

```
vllm-delivery-template/
├── serving/          # Server launch and configuration
├── client/           # Client examples and smoke tests
├── tests/            # pytest test suite
├── scripts/          # One-click startup scripts
└── docs/             # Detailed documentation
```

## Convenience Scripts

- `scripts/dev.sh` - One-click development startup (sets up venv, installs deps, starts server)
- `scripts/run_smoke_test.sh` - Run all tests (smoke test + pytest suite)
- `scripts/deploy_remote.sh` - Deploy to remote server with one command

## Documentation

- [Quick Start Guide](docs/quickstart.md) - Zero to running in 30 minutes
- [Configuration Reference](docs/configuration.md) - All config options explained
- [Ops Runbook](docs/ops_runbook.md) - Deployment and operations guide

## Requirements

- Python 3.10+
- CUDA-compatible GPU (for inference)
- uv (recommended) or pip for package management

## License

MIT
