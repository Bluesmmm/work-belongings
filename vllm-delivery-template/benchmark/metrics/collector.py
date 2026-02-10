#!/usr/bin/env python3
"""Prometheus metrics collector for vLLM benchmarking.

This module collects metrics from Prometheus during benchmark execution,
providing server-side performance data to complement client-side measurements.
"""

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import httpx


# vLLM Prometheus metrics queries
VLLM_QUERIES = {
    "request_throughput": 'rate(vllm:num_requests_total[{duration}s])',
    "avg_ttft": 'histogram_quantile(0.5, rate(vllm:time_to_first_token_seconds_bucket[{duration}s]))',
    "p95_ttft": 'histogram_quantile(0.95, rate(vllm:time_to_first_token_seconds_bucket[{duration}s]))',
    "avg_latency": 'histogram_quantile(0.5, rate(vllm:time_per_request_seconds_bucket[{duration}s]))',
    "p95_latency": 'histogram_quantile(0.95, rate(vllm:time_per_request_seconds_bucket[{duration}s]))',
    "gpu_cache_usage": 'avg(vllm:gpu_cache_usage_perc)',
    "queue_size": 'avg(vllm:waiting_queue_size)',
    "token_throughput": 'rate(vllm:num_generation_tokens[{duration}s])',
}


@dataclass
class PrometheusMetrics:
    """Collected metrics from Prometheus."""
    timestamp: str
    query_duration_seconds: float
    metrics: dict[str, Any]


class PrometheusCollector:
    """Collector for vLLM metrics from Prometheus."""

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """Initialize the Prometheus collector.

        Args:
            prometheus_url: URL of the Prometheus server
        """
        self.prometheus_url = prometheus_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def _build_query_url(self, query: str, start_time: float, end_time: float) -> str:
        """Build Prometheus query API URL.

        Args:
            query: PromQL query string
            start_time: Unix timestamp for query start
            end_time: Unix timestamp for query end

        Returns:
            Full URL for the Prometheus query API
        """
        encoded_query = httpx.URL(query).params.get("")
        return (
            f"{self.prometheus_url}/api/v1/query_range"
            f"?query={query}"
            f"&start={start_time}"
            f"&end={end_time}"
            f"&step=15s"
        )

    def query_prometheus(
        self,
        query: str,
        start_time: float,
        end_time: float,
    ) -> Optional[dict]:
        """Execute a query against Prometheus.

        Args:
            query: PromQL query string
            start_time: Unix timestamp for query start
            end_time: Unix timestamp for query end

        Returns:
            Query result as dictionary, or None if query fails
        """
        url = f"{self.prometheus_url}/api/v1/query_range"

        try:
            response = self.client.get(
                url,
                params={
                    "query": query,
                    "start": start_time,
                    "end": end_time,
                    "step": "15s",
                },
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":
                return data.get("data", {})
            return None

        except Exception as e:
            print(f"Warning: Prometheus query failed: {e}")
            return None

    def collect_vllm_metrics(
        self,
        test_start_time: float,
        test_end_time: float,
    ) -> PrometheusMetrics:
        """Collect all vLLM metrics for a test run.

        Args:
            test_start_time: Unix timestamp when test started
            test_end_time: Unix timestamp when test ended

        Returns:
            PrometheusMetrics with collected data
        """
        duration = test_end_time - test_start_time
        start_collect = time.time()

        metrics = {}

        # Add a small buffer to ensure we capture all data
        start_buffered = test_start_time - 5
        end_buffered = test_end_time + 5

        for metric_name, query_template in VLLM_QUERIES.items():
            query = query_template.format(duration=int(duration))
            result = self.query_prometheus(query, start_buffered, end_buffered)

            if result and result.get("result"):
                # Extract the value from the first result
                values = result["result"][0].get("values", [])
                if values:
                    # Get the average value across the time range
                    numeric_values = [float(v[1]) for v in values if v[1] != "None"]
                    if numeric_values:
                        metrics[metric_name] = sum(numeric_values) / len(numeric_values)
                    else:
                        metrics[metric_name] = 0.0
                else:
                    metrics[metric_name] = 0.0
            else:
                metrics[metric_name] = None  # Metric not available

        collect_duration = time.time() - start_collect

        return PrometheusMetrics(
            timestamp=datetime.now().isoformat(),
            query_duration_seconds=collect_duration,
            metrics=metrics,
        )

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def collect_metrics_if_enabled(
    prometheus_url: str,
    collect_enabled: bool,
    test_start_time: float,
    test_end_time: float,
) -> Optional[PrometheusMetrics]:
    """Collect Prometheus metrics if enabled.

    Convenience function that handles the case where Prometheus collection
    is disabled or unavailable.

    Args:
        prometheus_url: URL of the Prometheus server
        collect_enabled: Whether to collect metrics
        test_start_time: Unix timestamp when test started
        test_end_time: Unix timestamp when test ended

    Returns:
        PrometheusMetrics if collection succeeded, None otherwise
    """
    if not collect_enabled:
        return None

    try:
        with PrometheusCollector(prometheus_url) as collector:
            return collector.collect_vllm_metrics(test_start_time, test_end_time)
    except Exception as e:
        print(f"Warning: Failed to collect Prometheus metrics: {e}")
        return None
