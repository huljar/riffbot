from argparse import ArgumentParser, ArgumentTypeError, Namespace
from configparser import SafeConfigParser
from enum import Enum
import logging


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def _command_prefix(arg: str) -> str:
    if len(arg) != 1:
        raise ArgumentTypeError(f"Command prefix must be a single character (\"{arg}\" has {len(arg)} characters)")
    return arg


def parse_options() -> Namespace:
    conf_parser = ArgumentParser(add_help=False)
    conf_parser.add_argument("-c", "--config-file", help="Specify a config file (ini format)",
                             metavar="file")
    args, remaining_argv = conf_parser.parse_known_args()
    defaults = {
        "command_prefix": "!",
        "log_level": LogLevel.WARNING.name
    }
    if args.config_file:
        config = SafeConfigParser()
        config.read([args.config_file])
        defaults = {
            **vars(args),
            **defaults,
            **{key.replace("-", "_"): value for (key, value) in config.items("default")}
        }

    parser = ArgumentParser(parents=[conf_parser], description="RiffBot - Discord Music Bot")
    parser.set_defaults(**defaults)
    parser.add_argument("-p", "--command-prefix", type=str, help="Set the command prefix", metavar="prefix")
    parser.add_argument("-l", "--log-level", type=str.upper, choices=[level.name for level in list(LogLevel)],
                        help="Set the log level", metavar="level")
    args = parser.parse_args(remaining_argv)
    return args
