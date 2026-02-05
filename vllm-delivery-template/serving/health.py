"""Health check utilities for vLLM server."""

import time
from typing import Optional

import httpx


def check_health(base_url: str = "http://localhost:8000", timeout: int = 30) -> bool:
    """Check if the vLLM server is healthy.

    Args:
        base_url: Base URL of the vLLM server
        timeout: Maximum time to wait for server to be ready

    Returns:
        True if server is healthy, False otherwise
    """
    start = time.time()
    client = httpx.Client(timeout=5.0)

    while time.time() - start < timeout:
        try:
            response = client.get(f"{base_url}/health")
            if response.status_code == 200:
                return True
        except (httpx.ConnectError, httpx.ConnectTimeout):
            time.sleep(1)

    return False


def wait_for_ready(base_url: str = "http://localhost:8000", timeout: int = 30) -> None:
    """Wait for the vLLM server to be ready.

    Raises:
        TimeoutError: If server doesn't become ready within timeout
    """
    if not check_health(base_url, timeout):
        raise TimeoutError(f"Server not ready after {timeout} seconds")


def get_model_info(base_url: str = "http://localhost:8000") -> Optional[dict]:
    """Get model information from the server.

    Returns:
        Model info dict or None if request fails
    """
    client = httpx.Client(timeout=10.0)
    try:
        response = client.get(f"{base_url}/v1/models")
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, httpx.ConnectError):
        return None
