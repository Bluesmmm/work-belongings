#!/usr/bin/env python3
"""Smoke test for vLLM server.

This script verifies that the vLLM server is running and can respond
to basic chat completion requests using the OpenAI client.

Usage:
    python client/smoke_test.py
    python client/smoke_test.py --base-url http://localhost:9000 --api-key my-key
"""

import argparse
import sys
from typing import Optional

from openai import OpenAI


def smoke_test(
    base_url: str = "http://localhost:8000/v1",
    api_key: str = "token-abc123",
    model: str = "Qwen/Qwen2.5-3B-Instruct",
) -> bool:
    """Run smoke test against vLLM server.

    Args:
        base_url: Base URL of the vLLM server
        api_key: API key for authentication
        model: Model name to use in requests

    Returns:
        True if test passes, False otherwise
    """
    client = OpenAI(base_url=base_url, api_key=api_key)

    print(f"Connecting to: {base_url}")

    try:
        # Test 1: List models
        print("Test 1: Listing models...")
        models = client.models.list()
        print(f"  Available models: {[m.id for m in models.data]}")

        # Test 2: Simple chat completion
        print("Test 2: Simple chat completion...")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello! Please respond with 'OK'."}],
            max_tokens=50,
        )
        content = response.choices[0].message.content
        print(f"  Response: {content}")

        # Test 3: Streaming completion
        print("Test 3: Streaming completion...")
        stream = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Count from 1 to 3"}],
            max_tokens=50,
            stream=True,
        )
        chunks = []
        for chunk in stream:
            if chunk.choices[0].delta.content:
                chunks.append(chunk.choices[0].delta.content)
        print(f"  Streamed response: {''.join(chunks)}")

        print("✅ All smoke tests passed!")
        return True

    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run smoke test against vLLM server")
    parser.add_argument("--base-url", default="http://localhost:8000/v1", help="Server base URL")
    parser.add_argument("--api-key", default="token-abc123", help="API key")
    parser.add_argument("--model", default="Qwen/Qwen2.5-3B-Instruct", help="Model name")

    args = parser.parse_args()

    success = smoke_test(
        base_url=args.base_url,
        api_key=args.api_key,
        model=args.model,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
