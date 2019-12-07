"""
This module allows to control the application.
Some futures are already supported such as
start, stop, get and set value from database.

After starting application, there will be 3
different processes, one of them is MainProcess.

Process SlaveProcess: Downloads medias with given time sequence
Process MasterProcess: Shares the posts
"""
import sys
import time
import json
from threading import Thread

from instagram_database.db import Settings
from common.tools import raw_print, Q, \
    log_level_checker, autocomplate_input, COMPLATER
from common.logger import logger
from common.controller_helper import ConsoleCommandExecutor, \
    SLAVE_EXCEPTION_HANDLER, MASTER_EXCEPTION_HANDLER

COMPLATER.add_options(
    *[field.lower() for field in Settings.fields() if field != "id"]
)


def read_console_commands():
    "Waits for console inputs"

    console_executor = ConsoleCommandExecutor(Q)
    COMPLATER.add_options(*console_executor.callables)

    while console_executor:
        command = autocomplate_input(
            "Please enter the command: "
        ).strip().lower()

        console_executor(command)


def listen_exceptions():
    """
        Listens the queue. If any exception occurs
        in child processes, this block will terminate
        the program. If None received, means program
        terminated.
    """
    error = None
    while True:
        if SLAVE_EXCEPTION_HANDLER.qsize():
            error = SLAVE_EXCEPTION_HANDLER.get()
            break

        if MASTER_EXCEPTION_HANDLER.qsize():
            error = MASTER_EXCEPTION_HANDLER.get()
            break

        time.sleep(1)

    error = json.loads(error)
    if error is not None:
        raw_print(''.join(error))
    sys.exit()


def start_app():
    "Starts the application"
    Thread(
        target=read_console_commands,
        name="console_reader",
        daemon=True
    ).start()
    Thread(
        target=log_level_checker,
        args=(Q,),
        name="log_level_listener",
        daemon=True
    ).start()

    try:
        listen_exceptions()
    except (KeyboardInterrupt, EOFError):
        Q.state = False
        logger.warning("Application terminated")
