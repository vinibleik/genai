import asyncio
import time
from collections.abc import Callable
from concurrent.futures import Executor
from datetime import UTC, datetime
from typing import Any


def now_utc() -> datetime:
    return datetime.now(UTC)


async def asyncfy(
    func: Callable, *args: Any, executor: Executor | None = None, **kwargs: Any
):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, lambda: func(*args, **kwargs))


def timer(timeout: int) -> Callable[[], bool]:
    start = time.perf_counter_ns()

    def _func() -> bool:
        end = time.perf_counter_ns()
        total = int((end - start) * 1e-6)
        return total > timeout

    return _func
