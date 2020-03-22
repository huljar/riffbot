import logging
import os
import pathlib

from dotenv import load_dotenv
import i18n

from riffbot.bot import bot
from riffbot.options import LogLevel, parse_options


class TokenNotFoundError(Exception):
    pass


def main():
    # Get options (combined from defaults, config file, and command line arguments)
    options = parse_options()

    # Set up logging
    level = LogLevel[options.log_level].value
    logger = logging.getLogger(__package__)
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s (%(levelname)s) [%(name)s] %(message)s", "%m/%d/%Y %H:%M:%S")

    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)
    logger.setLevel(level)

    logger.debug(f"Combined options: {vars(options)}")

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

    # Set options and run the bot
    bot.command_prefix = options.command_prefix
    bot.run(token)


if __name__ == "__main__":
    main()
