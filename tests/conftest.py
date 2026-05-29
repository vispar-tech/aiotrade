"""Pytest config, fixtures, and shared test utilities for the test suite."""

import logging
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
from pytest import LogCaptureFixture

env_path = Path(".env.pytest")


@pytest.fixture(scope="session", autouse=True)
def load_pytest_env() -> None:
    """Automatically load .env.pytest file into os.environ before any tests run."""
    if env_path.exists():
        with env_path.open("r") as f:
            for raw_line in f:
                clean_line = raw_line.strip()
                if (
                    not clean_line
                    or clean_line.startswith("#")
                    or "=" not in clean_line
                ):
                    continue
                key, val = clean_line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())


@pytest.fixture(scope="session")
def proxy_url() -> str:
    """Fixture providing the PROXY_URL from environment (after loading .env.pytest)."""
    return os.environ.get("PROXY_URL", "")


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Pytest fixture to specify the backend for the anyio plugin.

    Returns:
        str: The name of the backend to use ("asyncio").
    """
    return "asyncio"


@pytest.fixture(autouse=True)
def setup_logging(caplog: LogCaptureFixture) -> Generator[None, Any, None]:
    """Set up and configure logging for each test.

    Capture all logs and set log level to DEBUG.

    Args:
        caplog (LogCaptureFixture): Built-in pytest fixture for capturing log messages.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)8s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,  # Reset handlers for test isolation
    )
    caplog.set_level(logging.DEBUG)
    yield
