"""Pytest tests for vLLM server smoke tests.

Usage:
    pytest tests/test_smoke.py
    pytest tests/test_smoke.py -v
"""

import pytest
from openai import OpenAI


@pytest.fixture
def client():
    """Create OpenAI client for testing."""
    return OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="token-abc123",
    )


def test_server_responds(client: OpenAI):
    """Test that server responds to basic requests."""
    response = client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "Say 'test passed'"}],
        max_tokens=50,
    )

    assert response.choices[0].message.content is not None
    assert len(response.choices[0].message.content) > 0


def test_streaming_works(client: OpenAI):
    """Test that streaming responses work."""
    stream = client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=50,
        stream=True,
    )

    chunks = []
    for chunk in stream:
        if chunk.choices[0].delta.content:
            chunks.append(chunk.choices[0].delta.content)

    assert len(chunks) > 0


def test_max_tokens_respected(client: OpenAI):
    """Test that max_tokens parameter is respected."""
    max_tokens = 10
    response = client.chat.completions.create(
        model="test-model",
        messages=[{"role": "user", "content": "Write a long paragraph"}],
        max_tokens=max_tokens,
    )

    # Response should not exceed max_tokens significantly
    # (token count may differ slightly from character count)
    content = response.choices[0].message.content
    assert content is not None
    assert len(content) < max_tokens * 10  # Rough estimate


def test_system_message(client: OpenAI):
    """Test that system messages are handled correctly."""
    response = client.chat.completions.create(
        model="test-model",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who always ends with '!'"},
            {"role": "user", "content": "Say hello"},
        ],
        max_tokens=50,
    )

    assert response.choices[0].message.content is not None
