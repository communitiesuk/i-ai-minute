import asyncio

import pytest
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.example")


@pytest.fixture(scope="session")
def event_loop_policy() -> asyncio.AbstractEventLoopPolicy:
    return asyncio.get_event_loop_policy()
