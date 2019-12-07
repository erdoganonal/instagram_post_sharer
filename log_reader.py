"Prints the log file. Allows some filters."
import os
import argparse
import time

import colorama
from colorama import Fore

from settings import FILENAME

colorama.init()

LEVEL_COLOR_DICT = {
    "DEBUG": Fore.BLUE,
    "INFO":  Fore.GREEN,
    "WARNING": Fore.YELLOW,
    "ERROR": Fore.RED,
    "CRITICAL": Fore.RED
}

LEVELS = {
    "CRITICAL": 50,
    "FATAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
}

ALL = "All"
PROCESS_NAMES = (
    "MainProcess",
    "SlaveInstagram",
    "MasterInstagram",
    ALL
)


MESSAGE_FORMAT = (
    "{0:10}"  # Level
    "{1:17}"  # Process Name
    "{2:25}"  # Filename
    "{3:25}"  # Function Name
    "{4:5}"   # Line
    "{5}"     # Message
)


def main():
    "Starts from here"
    os.system("cls")
    logfile = open(FILENAME, 'r')
    logs = tailf(logfile)
    colored_message = MESSAGE_FORMAT.format(
        "Level", "Process Name",
        "Filename", "Function Name", "Line", "Message"
    )
    print(colored_message)
    for log in logs:
        display_log(log)


def display_log(log):
    "Prints the log to the screen"
    try:
        level, process_name, filename, \
            function_name, line, _, *message = log.split(':')
    except ValueError:
        # ValueError means, incoming message has multiple lines.
        # This only occurs with message with new lines and
        # on exception. Since the API has no message with
        # new lines, only possible thing is exception.
        # Since the entire exception levels are error or
        # critical, the color of message should be red.
        print(f"{Fore.RED}{log}{Fore.RESET}", end='')
        return

    if is_filtered(level, process_name, filename, function_name, line):
        return

    message = ':'.join(message)
    color = LEVEL_COLOR_DICT[level]

    colored_message = color + MESSAGE_FORMAT.format(
        level, process_name, filename,
        function_name, line, message
    ) + Fore.RESET

    print(colored_message, end='')


def _is_filtered(value, from_arg):
    return not (value in from_arg or from_arg == ALL)


def is_filtered(level, process_name, filename, function_name, line):
    "Checks the log filtered or not"
    if LEVELS[level] < ARGS.log_level:
        return True

    if _is_filtered(process_name, ARGS.process_name):
        return True

    if _is_filtered(filename, ARGS.filename):
        return True

    if _is_filtered(function_name, ARGS.function_name):
        return True

    if not line:
        return True

    return False


def tailf(filename):
    "tails the file"
    while True:
        try:
            line = filename.readline()
            if not line or not line.endswith('\n'):
                time.sleep(0.1)
                continue
            yield line
        except KeyboardInterrupt:
            break


def log_level_validator(level):
    "The validator of log level"
    level = level.upper()
    if level not in LEVELS.keys():
        raise argparse.ArgumentTypeError(
            "invalid choice: '{0}' (choose from {1})".format(
                level, ', '.join(LEVELS.keys())
            )
        )

    return LEVELS[level]


def get_args():
    "Parses the arguments"
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-l", "--log-level",
        nargs=None,
        required=False,
        type=log_level_validator,
        metavar='',
        default=LEVELS["DEBUG"]
    )

    parser.add_argument(
        "-p", "--process-name",
        nargs=argparse.ONE_OR_MORE,
        required=False,
        choices=PROCESS_NAMES,
        metavar='',
        default=ALL
    )

    parser.add_argument(
        "--filename",
        nargs=argparse.ONE_OR_MORE,
        required=False,
        metavar='',
        default=ALL
    )

    parser.add_argument(
        "--function-name",
        nargs=argparse.ONE_OR_MORE,
        required=False,
        metavar='',
        default=ALL
    )

    return parser.parse_args()


ARGS = get_args()


if __name__ == "__main__":
    main()
