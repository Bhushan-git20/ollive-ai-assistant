"""
Shared pytest fixtures for Ollive AI test suite.
Run from project root: pytest tests/
"""

import pytest
import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Global mocks for missing dependencies
from unittest.mock import MagicMock
sys.modules['duckduckgo_search'] = MagicMock()


@pytest.fixture
def safe_messages():
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thanks!"},
        {"role": "user", "content": "What is 2 + 2?"},
    ]


@pytest.fixture
def empty_history():
    return []


@pytest.fixture
def single_user_history():
    return [{"role": "user", "content": "Hello"}]
