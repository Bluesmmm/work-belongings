#!/usr/bin/env python3
"""Load testing script for vLLM server.

This script performs concurrent load testing against a vLLM server,
collecting performance metrics such as throughput, latency, and time-to-first-token.

Usage:
    python benchmark/load_test.py
    python benchmark/load_test.py --config benchmark/config/default.yaml
    python benchmark/load_test.py --concurrency 20 --num-requests 500
"""

import argparse
import asyncio
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx


@dataclass
class RequestMetrics:
    """Metrics collected for a single request."""
    request_id: str
    start_time: float
    end_time: float
    ttft_ms: float = 0.0              # Time to First Token in milliseconds
    e2e_latency_ms: float = 0.0       # End-to-end latency in milliseconds
    output_tokens: int = 0
    input_tokens: int = 0
    tokens_per_second: float = 0.0
    error: Optional[str] = None


@dataclass
class TestResult:
    """Aggregated results from a load test."""
    config: dict
    timestamp: str
    duration_seconds: float
    total_requests: int
    successful_requests: int
    failed_requests: int
    throughput_rps: float
    request_metrics: list[RequestMetrics] = field(default_factory=list)


@dataclass
class Statistics:
    """Statistical summary of metrics."""
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_ttft_ms: float
    p50_ttft_ms: float
    p95_ttft_ms: float
    p99_ttft_ms: float
    avg_tokens_per_second: float
    throughput_rps: float


def load_config(config_path: str) -> dict:
    """Load configuration from YAML file."""
    import yaml
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_prompt(config: dict) -> str:
    """Generate a test prompt based on configuration.

    For load testing, we generate prompts that approximate the target token length.
    """
    prompt_type = config.get("prompt", {}).get("prompt_type", "random")
    input_length = config.get("prompt", {}).get("input_length", 512)

    if prompt_type == "fixed":
        fixed = config.get("prompt", {}).get("fixed_prompt", "")
        if fixed:
            return fixed

    # Generate a prompt that approximately targets the input length
    # This is a rough approximation - actual token count depends on the model's tokenizer
    base_phrase = "Please explain the following concept in detail: "
    topics = [
        "quantum computing and its applications",
        "machine learning model architectures",
        "distributed systems design patterns",
        "natural language processing techniques",
        "computer vision algorithms",
        "database optimization strategies",
        "microservices architecture principles",
        "cloud infrastructure management",
        "data structures and algorithms",
        "software engineering best practices",
    ]

    import random
    topic = random.choice(topics)
    prompt = f"{base_phrase}{topic}. "

    # Approximate: each word ~1.3 tokens, each character ~0.3 tokens
    # Repeat to reach target length
    while len(prompt) * 0.3 < input_length:
        prompt += f"Elaborate on {topic}. "

    return prompt[:int(input_length * 3)]  # Rough character limit


async def send_request(
    client: httpx.AsyncClient,
    request_id: str,
    prompt: str,
    config: dict,
) -> RequestMetrics:
    """Send a single request and collect metrics.

    Uses streaming to accurately measure Time to First Token (TTFT).
    """
    server_config = config.get("server", {})
    load_config = config.get("load", {})

    base_url = server_config.get("base_url", "http://localhost:8000/v1")
    model = server_config.get("model", "Qwen/Qwen2.5-3B-Instruct")
    max_tokens = config.get("prompt", {}).get("output_length", 128)
    timeout = load_config.get("request_timeout", 120)

    url = f"{base_url}/chat/completions"
    headers = {"Authorization": f"Bearer {server_config.get('api_key', 'token-abc123')}"}

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "stream": True,  # Use streaming for TTFT measurement
    }

    metrics = RequestMetrics(
        request_id=request_id,
        start_time=time.time(),
        end_time=0.0,
    )

    try:
        start = time.time()
        first_token_time = None
        output_text = []

        async with client.stream("POST", url, json=payload, headers=headers, timeout=timeout) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise Exception(f"HTTP {response.status_code}: {error_text.decode()}")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")

                        if content and first_token_time is None:
                            first_token_time = time.time()

                        output_text.append(content)
                    except json.JSONDecodeError:
                        pass

        end = time.time()
        output_content = "".join(output_text)

        # Estimate token counts (rough approximation: ~4 chars per token)
        metrics.input_tokens = int(len(prompt) / 4)
        metrics.output_tokens = int(len(output_content) / 4)

        metrics.ttft_ms = (first_token_time - start) * 1000 if first_token_time else 0
        metrics.e2e_latency_ms = (end - start) * 1000
        metrics.end_time = end

        if metrics.e2e_latency_ms > 0:
            metrics.tokens_per_second = (metrics.output_tokens / metrics.e2e_latency_ms) * 1000

    except Exception as e:
        metrics.error = str(e)
        metrics.end_time = time.time()

    return metrics


async def run_concurrent_test(config: dict) -> TestResult:
    """Run load test with concurrent requests."""
    load_config = config.get("load", {})
    concurrency = load_config.get("concurrency", 10)
    num_requests = load_config.get("num_requests", 100)
    warmup_requests = load_config.get("warmup_requests", 10)

    print(f"Starting load test: {num_requests} requests with concurrency {concurrency}")

    # Warmup phase
    if warmup_requests > 0:
        print(f"Warmup: {warmup_requests} requests...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            warmup_tasks = []
            for i in range(warmup_requests):
                prompt = generate_prompt(config)
                task = send_request(client, f"warmup-{i}", prompt, config)
                warmup_tasks.append(task)
            await asyncio.gather(*warmup_tasks)
        print("Warmup complete.")

    # Main test phase
    start_time = time.time()
    all_metrics = []

    async with httpx.AsyncClient(timeout=120.0) as client:
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)

        async def bounded_request(idx: int) -> RequestMetrics:
            async with semaphore:
                prompt = generate_prompt(config)
                return await send_request(client, f"req-{idx}", prompt, config)

        # Launch all requests concurrently
        tasks = [bounded_request(i) for i in range(num_requests)]
        all_metrics = await asyncio.gather(*tasks)

    end_time = time.time()
    duration = end_time - start_time

    # Separate successful and failed requests
    successful = [m for m in all_metrics if not m.error]
    failed = [m for m in all_metrics if m.error]

    # Calculate throughput
    throughput_rps = len(successful) / duration if duration > 0 else 0

    result = TestResult(
        config=config,
        timestamp=datetime.now().isoformat(),
        duration_seconds=duration,
        total_requests=num_requests,
        successful_requests=len(successful),
        failed_requests=len(failed),
        throughput_rps=throughput_rps,
        request_metrics=successful,
    )

    # Print summary
    print(f"\n=== Load Test Complete ===")
    print(f"Duration: {duration:.2f}s")
    print(f"Throughput: {throughput_rps:.2f} req/s")
    print(f"Successful: {len(successful)}/{num_requests}")
    print(f"Failed: {len(failed)}/{num_requests}")

    if failed:
        print(f"\nSample errors:")
        for m in failed[:3]:
            print(f"  - {m.error}")

    return result


def calculate_statistics(metrics: list[RequestMetrics], throughput_rps: float) -> Statistics:
    """Calculate statistical summary from request metrics."""
    if not metrics:
        return Statistics(
            avg_latency_ms=0,
            p50_latency_ms=0,
            p95_latency_ms=0,
            p99_latency_ms=0,
            avg_ttft_ms=0,
            p50_ttft_ms=0,
            p95_ttft_ms=0,
            p99_ttft_ms=0,
            avg_tokens_per_second=0,
            throughput_rps=throughput_rps,
        )

    import numpy as np

    latencies = [m.e2e_latency_ms for m in metrics if m.e2e_latency_ms > 0]
    ttfts = [m.ttft_ms for m in metrics if m.ttft_ms > 0]
    tps = [m.tokens_per_second for m in metrics if m.tokens_per_second > 0]

    def percentile(data: list[float], p: int) -> float:
        return float(np.percentile(data, p)) if data else 0.0

    return Statistics(
        avg_latency_ms=float(np.mean(latencies)) if latencies else 0.0,
        p50_latency_ms=percentile(latencies, 50),
        p95_latency_ms=percentile(latencies, 95),
        p99_latency_ms=percentile(latencies, 99),
        avg_ttft_ms=float(np.mean(ttfts)) if ttfts else 0.0,
        p50_ttft_ms=percentile(ttfts, 50),
        p95_ttft_ms=percentile(ttfts, 95),
        p99_ttft_ms=percentile(ttfts, 99),
        avg_tokens_per_second=float(np.mean(tps)) if tps else 0.0,
        throughput_rps=throughput_rps,
    )


def main():
    parser = argparse.ArgumentParser(description="Run load test against vLLM server")
    parser.add_argument(
        "--config",
        default="benchmark/config/default.yaml",
        help="Path to benchmark configuration file"
    )
    parser.add_argument("--concurrency", type=int, help="Override concurrency level")
    parser.add_argument("--num-requests", type=int, help="Override number of requests")
    parser.add_argument("--output", help="Output directory for reports")

    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Apply CLI overrides
    if args.concurrency is not None:
        config.setdefault("load", {})["concurrency"] = args.concurrency
    if args.num_requests is not None:
        config.setdefault("load", {})["num_requests"] = args.num_requests

    # Run test
    result = asyncio.run(run_concurrent_test(config))

    # Calculate statistics
    stats = calculate_statistics(result.request_metrics, result.throughput_rps)

    print(f"\n=== Statistics ===")
    print(f"Latency (ms):  avg={stats.avg_latency_ms:.1f}  p50={stats.p50_latency_ms:.1f}  p95={stats.p95_latency_ms:.1f}  p99={stats.p99_latency_ms:.1f}")
    print(f"TTFT (ms):    avg={stats.avg_ttft_ms:.1f}  p50={stats.p50_ttft_ms:.1f}  p95={stats.p95_ttft_ms:.1f}  p99={stats.p99_ttft_ms:.1f}")
    print(f"Tokens/sec:   {stats.avg_tokens_per_second:.1f}")

    # Save JSON report
    output_dir = Path(args.output or config.get("report", {}).get("output_dir", "benchmark/reports"))
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = output_dir / f"benchmark_{timestamp}.json"

    report_data = {
        "metadata": {
            "timestamp": result.timestamp,
            "config": config,
        },
        "summary": {
            "duration_seconds": result.duration_seconds,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "failed_requests": result.failed_requests,
            "throughput_rps": result.throughput_rps,
        },
        "latency": {
            "avg_ms": stats.avg_latency_ms,
            "p50_ms": stats.p50_latency_ms,
            "p95_ms": stats.p95_latency_ms,
            "p99_ms": stats.p99_latency_ms,
        },
        "ttft": {
            "avg_ms": stats.avg_ttft_ms,
            "p50_ms": stats.p50_ttft_ms,
            "p95_ms": stats.p95_ttft_ms,
            "p99_ms": stats.p99_ttft_ms,
        },
        "throughput": {
            "tokens_per_second": stats.avg_tokens_per_second,
        },
    }

    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nJSON report saved to: {json_path}")

    sys.exit(0 if result.failed_requests == 0 else 1)


if __name__ == "__main__":
    main()
