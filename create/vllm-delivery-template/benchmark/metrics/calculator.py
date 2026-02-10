#!/usr/bin/env python3
"""Statistical calculations for benchmark metrics.

This module provides functions for computing percentiles, means, standard deviations,
and other statistics from benchmark request metrics.
"""

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class LatencyStatistics:
    """Statistical summary of latency measurements."""
    avg_ms: float
    min_ms: float
    max_ms: float
    std_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float


@dataclass
class ThroughputStatistics:
    """Statistical summary of throughput measurements."""
    requests_per_second: float
    tokens_per_second: float
    total_tokens: int


def calculate_percentiles(values: list[float], percentiles: list[int]) -> dict[int, float]:
    """Calculate percentiles for a list of values.

    Args:
        values: List of numerical values
        percentiles: List of percentiles to calculate (e.g., [50, 95, 99])

    Returns:
        Dictionary mapping percentile to value
    """
    if not values:
        return {p: 0.0 for p in percentiles}

    return {p: float(np.percentile(values, p)) for p in percentiles}


def calculate_mean(values: list[float]) -> float:
    """Calculate arithmetic mean of values.

    Args:
        values: List of numerical values

    Returns:
        Mean value, or 0.0 if list is empty
    """
    if not values:
        return 0.0
    return float(np.mean(values))


def calculate_stddev(values: list[float]) -> float:
    """Calculate standard deviation of values.

    Args:
        values: List of numerical values

    Returns:
        Standard deviation, or 0.0 if list has fewer than 2 elements
    """
    if len(values) < 2:
        return 0.0
    return float(np.std(values, ddof=1))


def calculate_coefficient_of_variation(values: list[float]) -> float:
    """Calculate coefficient of variation (CV).

    CV is the ratio of standard deviation to mean, expressed as a percentage.
    This is useful for measuring relative variability.

    Args:
        values: List of numerical values

    Returns:
        CV as a percentage, or 0.0 if mean is 0
    """
    mean = calculate_mean(values)
    if mean == 0:
        return 0.0
    return (calculate_stddev(values) / mean) * 100


def calculate_latency_statistics(
    latencies_ms: list[float],
    percentiles: Optional[list[int]] = None,
) -> LatencyStatistics:
    """Calculate comprehensive latency statistics.

    Args:
        latencies_ms: List of latency values in milliseconds
        percentiles: Custom percentiles to calculate (default: [50, 90, 95, 99])

    Returns:
        LatencyStatistics dataclass with all computed values
    """
    if percentiles is None:
        percentiles = [50, 90, 95, 99]

    if not latencies_ms:
        return LatencyStatistics(
            avg_ms=0.0,
            min_ms=0.0,
            max_ms=0.0,
            std_ms=0.0,
            p50_ms=0.0,
            p90_ms=0.0,
            p95_ms=0.0,
            p99_ms=0.0,
        )

    percentiles_dict = calculate_percentiles(latencies_ms, percentiles)

    return LatencyStatistics(
        avg_ms=calculate_mean(latencies_ms),
        min_ms=float(np.min(latencies_ms)),
        max_ms=float(np.max(latencies_ms)),
        std_ms=calculate_stddev(latencies_ms),
        p50_ms=percentiles_dict.get(50, 0.0),
        p90_ms=percentiles_dict.get(90, 0.0),
        p95_ms=percentiles_dict.get(95, 0.0),
        p99_ms=percentiles_dict.get(99, 0.0),
    )


def verify_reproducibility(
    throughput_values: list[float],
    max_cv_percent: float = 10.0,
) -> tuple[bool, float, str]:
    """Verify that benchmark results are reproducible within acceptable variance.

    Args:
        throughput_values: List of throughput measurements from multiple runs
        max_cv_percent: Maximum acceptable coefficient of variation (default: 10%)

    Returns:
        Tuple of (is_reproducible, cv_percent, message)
    """
    if len(throughput_values) < 2:
        return True, 0.0, "Insufficient data for variance check"

    cv = calculate_coefficient_of_variation(throughput_values)
    mean = calculate_mean(throughput_values)

    if cv <= max_cv_percent:
        return True, cv, f"Variance within limits (CV: {cv:.2f}% <= {max_cv_percent}%)"
    else:
        return False, cv, f"Variance too high (CV: {cv:.2f}% > {max_cv_percent}%)"
