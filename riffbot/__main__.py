import argparse
from enum import Enum
import logging
import os

from dotenv import load_dotenv

from riffbot.bot import bot


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def main():
    # Parse command line arguments
    cmdparser = argparse.ArgumentParser(description="Riffbot - Discord Music Bot")
    cmdparser.add_argument("--log", nargs=1, default=[LogLevel.WARNING.name], type=str,
                           choices=[level.name for level in list(LogLevel)], help="log level (default: WARNING)",
                           metavar="LEVEL")
    args = cmdparser.parse_args()

    # Set up logging
    level = LogLevel[args.log[0]].value
    logger = logging.getLogger(__package__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(name)s] (%(levelname)s) %(message)s", "%m/%d/%Y %H:%M:%S")

    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)

    # Read environment variables from .env file
    load_dotenv()
    # Load the discord authorization token from DISCORD_TOKEN environment variable
    token = os.getenv("DISCORD_TOKEN")

    # Run the bot
    bot.run(token)


if __name__ == "__main__":
    main()
