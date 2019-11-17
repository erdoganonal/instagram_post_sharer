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
import urllib
import time
import traceback
import json
from threading import Thread
from multiprocessing import Process, Queue

import settings
from common.tools import set_proxy, raw_print, \
    clean, Q, log_level_checker, autocomplate_input, COMPLATER
from common.logger import logger
from instagram.master import MasterInstagram
from instagram.slave import SlaveInstagram
from instagram_database.db import Settings, \
    set_realtime_setting, get_realtime_setting


SLAVE_EXCEPTION_HANDLER = Queue()
MASTER_EXCEPTION_HANDLER = Queue()
COMPLATER.add_options(
    "get", "set",
    "start", "stop", "exit", "terminate"
)
COMPLATER.add_options(
    *[field.lower() for field in Settings.fields() if field != "id"]
)


def module_process_starter(instagram_class, queue, exception_handler):
    "A function for creating the module in Process"
    instagram = instagram_class(
        username=settings.SLAVE_USERNAME,
        password=settings.SLAVE_PASSWORD,
        queue=queue
    )

    try:
        urllib.request.urlopen("http://www.google.com", timeout=1)
    except urllib.error.URLError:
        set_proxy(instagram)

    # pylint:disable=bare-except
    try:
        instagram.start()
    except:
        exc_info = sys.exc_info()
        logger.critical("Exception::", exc_info=True)
        exception_handler.put(
            json.dumps(traceback.format_exception(*exc_info))
        )


def _handle_set_command(name, value):
    try:
        set_realtime_setting(name.upper(), value)
    except (AttributeError, ValueError):
        traceback.print_exc()


def _handle_get_command(name):
    try:
        return get_realtime_setting(name.upper())
    except AttributeError:
        traceback.print_exc()


def _handle_if_valid(command):
    if command.startswith("set"):
        command = command.lstrip("set").split()
        # command should be like `set name value`
        if len(command) == 2:
            _handle_set_command(*command)
        else:
            raw_print("set command must have 2 arguments")
    elif command.startswith("get"):
        command = command.lstrip("get").split()
        # command should be like `set name value`
        if len(command) == 1:
            raw_print(_handle_get_command(*command))
        else:
            raw_print("get command must have 1 argument")
    else:
        return False

    return True


def _start():
    Q.state = True

    slave, master = _create_processes()

    logger.debug("Application starting...")
    slave.start()
    master.start()
    logger.debug("Application started")

    return slave, master


def _stop(slave, master):
    Q.state = False

    if slave:
        slave.join()
    if master:
        master.join()

    logger.warning("Application stopped.")


def _terminate(slave, master):
    Q.state = False
    try:
        slave.terminate()
    except AttributeError:
        pass

    try:
        master.terminate()
    except AttributeError:
        pass

    SLAVE_EXCEPTION_HANDLER.put(
        json.dumps(None)
    )

    MASTER_EXCEPTION_HANDLER.put(
        json.dumps(None)
    )


def _create_processes():
    slave_instagram = Process(
        target=module_process_starter,
        args=(SlaveInstagram, Q, SLAVE_EXCEPTION_HANDLER),
        name="SlaveInstagram",
        daemon=True
    )
    master_instagram = Process(
        target=module_process_starter,
        args=(MasterInstagram, Q, MASTER_EXCEPTION_HANDLER),
        name="MasterInstagram",
        daemon=True
    )

    return slave_instagram, master_instagram


def read_console_commands():
    "Waits for console inputs"
    slave, master = None, None

    while True:
        command = autocomplate_input(
            "Please enter the command: "
        ).strip().lower()

        if command == "start":
            if (slave and slave.is_alive()) and (master and master.is_alive()):
                raw_print("Processes are already running!")
            else:
                slave, master = _start()
        elif command in ("stop", "exit"):
            _stop(slave, master)
            if command == "exit":
                _terminate(slave, master)
                break
        elif command == "terminate":
            _terminate(slave, master)
            break
        elif command == "reload":
            _stop(slave, master)
            slave, master = _start()
        elif command == "clear":
            clean()
        elif _handle_if_valid(command):
            pass
        else:
            raw_print("Unknown command!")


def listen_exceptions():
    """
        Listens the queue. If any exception occurs
        in child processes, this block will terminate
        the program.
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
