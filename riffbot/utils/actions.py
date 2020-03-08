from functools import reduce, wraps
from logging import Logger
from typing import Any, Awaitable, Callable

from discord.ext.commands import Context


def log_command(logger: Logger):
    def decorator(command: Callable[..., Awaitable[None]]):
        @wraps(command)
        async def with_logging(ctx: Context, *args: Any, **kwargs: Any):
            sanitized_args = map(lambda arg: str(arg), filter(lambda arg: arg is not None, args))
            kwargs_string = reduce(lambda acc, val: f"{acc} {val[0]}={val[1]}", kwargs.items(), "")[1:]
            logger.info(f"Received command \"{' '.join([command.__name__, *sanitized_args, kwargs_string]).strip()}\""
                        f" from {ctx.author.name}")
            return await command(ctx, *args, **kwargs)
        return with_logging
    return decorator
