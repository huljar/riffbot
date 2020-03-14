import argparse
from enum import Enum
import logging
import os
import pathlib

from dotenv import load_dotenv
import i18n

from riffbot.bot import bot


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class TokenNotFoundError(Exception):
    pass


def main():
    # Parse command line arguments
    cmdparser = argparse.ArgumentParser(description="Riffbot - Discord Music Bot")
    cmdparser.add_argument("--log", nargs=1, default=[LogLevel.WARNING.name], type=str,
                           choices=[level.name for level in list(LogLevel)], help="log level (default: WARNING)",
                           metavar="LEVEL")
    args = cmdparser.parse_args()

    # Set up logging
    level = LogLevel[args.log[0].upper()].value
    logger = logging.getLogger(__package__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s (%(levelname)s) [%(name)s] %(message)s", "%m/%d/%Y %H:%M:%S")

    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)

    # Set up i18n
    i18n.set("locale", "en_US")
    i18n.set("fallback", "en_US")
    i18n.set("enable_memoization", True)
    strings_path = pathlib.Path(__file__).parent.absolute().joinpath("strings")
    i18n.load_path.append(str(strings_path))

    # Read environment variables from .env file
    load_dotenv()
    # Load the discord authorization token from DISCORD_TOKEN environment variable
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise TokenNotFoundError()

    # Run the bot
    bot.run(token)


if __name__ == "__main__":
    main()
