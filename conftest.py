import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    return asyncio.get_event_loop_policy()
