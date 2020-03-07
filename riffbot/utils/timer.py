import asyncio
from typing import Any, Awaitable, Callable


class Timer:
    def __init__(self, timeout: float, callback: Callable[..., Awaitable[None]], *args: Any, **kwargs: Any):
        self._timeout = timeout
        self._callback = callback
        self._args = args
        self._kwargs = kwargs
        self._task = asyncio.ensure_future(self._job())

    async def _job(self):
        await asyncio.sleep(self._timeout)
        await self._callback(*self._args, **self._kwargs)

    def cancel(self):
        self._task.cancel()

    def reset_timeout(self):
        self._task.cancel()
        self._task = asyncio.ensure_future(self._job())
