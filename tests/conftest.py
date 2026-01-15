"""Pytest config, fixtures, and shared test utilities for the test suite."""

import logging
from typing import Any, Generator

import pytest
from pytest import LogCaptureFixture


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
