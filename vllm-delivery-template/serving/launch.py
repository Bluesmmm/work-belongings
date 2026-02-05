#!/usr/bin/env python3
"""vLLM server launcher.

This script provides a convenient wrapper around the vllm serve command
with YAML-based configuration management.

Usage:
    python serving/launch.py
    python serving/launch.py --config serving/config.yaml
    python serving/launch.py --port 9000 --gpu-memory-utilization 0.95
"""

import argparse
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: uv pip install pyyaml")
    sys.exit(1)


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_command(config: dict) -> list[str]:
    """Build vllm serve command from configuration."""
    cmd = [
        "vllm", "serve", config["model"],
        "--port", str(config.get("port", 8000)),
        "--api-key", config.get("api_key", "token-abc123"),
        "--dtype", config.get("dtype", "auto"),
        "--gpu-memory-utilization", str(config.get("gpu_memory_utilization", 0.9)),
        "--max-model-len", str(config.get("max_model_len", 8192)),
    ]

    # Optional advanced parameters
    if config.get("enforce_eager", False):
        cmd.append("--enforce-eager")
    if "tensor_parallel_size" in config:
        cmd.extend(["--tensor-parallel-size", str(config["tensor_parallel_size"])])
    if "block_size" in config:
        cmd.extend(["--block-size", str(config["block_size"])])
    if "swap_space" in config:
        cmd.extend(["--swap-space", str(config["swap_space"])])
    if "max_num_batched_tokens" in config:
        cmd.extend(["--max-num-batched-tokens", str(config["max_num_batched_tokens"])])
    if "max_num_seqs" in config:
        cmd.extend(["--max-num-seqs", str(config["max_num_seqs"])])

    return cmd


def main():
    parser = argparse.ArgumentParser(description="Launch vLLM server with YAML config")
    parser.add_argument(
        "--config",
        default="serving/config.yaml",
        help="Path to configuration file (default: serving/config.yaml)"
    )
    parser.add_argument("--port", type=int, help="Override server port")
    parser.add_argument("--gpu-memory-utilization", type=float, help="Override GPU memory utilization")
    parser.add_argument("--max-model-len", type=int, help="Override maximum model length")
    parser.add_argument("--enforce-eager", action="store_true", help="Disable CUDA graph compilation (use eager mode)")

    args = parser.parse_args()

    # Load base configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Apply CLI overrides
    if args.port is not None:
        config["port"] = args.port
    if args.gpu_memory_utilization is not None:
        config["gpu_memory_utilization"] = args.gpu_memory_utilization
    if args.max_model_len is not None:
        config["max_model_len"] = args.max_model_len
    if args.enforce_eager:
        config["enforce_eager"] = True

    # Build and execute command
    cmd = build_command(config)
    print(f"Starting vLLM server: {' '.join(cmd)}")
    print(f"Model: {config['model']}")
    print(f"Port: {config['port']}")

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running vLLM: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
