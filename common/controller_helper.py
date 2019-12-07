"""
A helper for executing commands coming
from console
"""
import sys
import os
import urllib
import traceback
import shutil
import json
from multiprocessing import Process, Queue

import settings
from common.tools import set_proxy, raw_print
from common.logger import logger
from instagram.master import MasterInstagram
from instagram.slave import SlaveInstagram
from instagram_database.db import set_realtime_setting, get_realtime_setting

SLAVE_EXCEPTION_HANDLER = Queue()
MASTER_EXCEPTION_HANDLER = Queue()


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


class ConsoleCommandExecutor:
    "execute commands coming from console"
    __callables__ = [
        'clean', 'clear',
        'get', 'set',
        'hardreload', 'help',
        'start', 'stop', 'reload',
        'terminate', 'exit',
    ]

    def __init__(self, queue):
        self.slave = None
        self.master = None
        self.queue = queue
        self.is_active = True

    def _stop_queue(self):
        SLAVE_EXCEPTION_HANDLER.put(json.dumps(None))
        MASTER_EXCEPTION_HANDLER.put(json.dumps(None))
        self.is_active = False

    def call(self, text):
        "call the related function from string"
        try:
            command, *options = text.split()
        except ValueError:
            return

        try:
            if command not in self.__callables__:
                raise AttributeError
            getattr(self, command)(*options)
        except ZeroDivisionError:
            raw_print("Unknown command.")
        except TypeError:
            raw_print(
                "Invalid argument. Type `help {0}` for help".format(command))

    def __call__(self, text):
        "call the related function from string"
        self.call(text)

    def _create_processes(self):
        slave_instagram = Process(
            target=module_process_starter,
            args=(SlaveInstagram, self.queue, SLAVE_EXCEPTION_HANDLER),
            name="SlaveInstagram",
            daemon=True
        )
        master_instagram = Process(
            target=module_process_starter,
            args=(MasterInstagram, self.queue, MASTER_EXCEPTION_HANDLER),
            name="MasterInstagram",
            daemon=True
        )

        return slave_instagram, master_instagram

    def start(self, *_):
        "start the application"
        self.queue.state = True

        if self.slave and self.slave.is_alive() and self.master and self.master.is_alive():
            raw_print("Application is already running!")
            return

        self.slave, self.master = self._create_processes()

        logger.debug("Application starting...")
        self.slave.start()
        self.master.start()
        logger.debug("Application started")

    def stop(self, *_):
        "stop the application"
        self.queue.state = False

        if self.slave:
            self.slave.join()
        if self.master:
            self.master.join()

        logger.warning("Application stopped.")

    def exit(self, *options):
        "stop the application and exit"
        self.stop(*options)
        self._stop_queue()

    def terminate(self, *_, exit_=True):
        "stop the application immediately"
        self.queue.state = False
        try:
            self.slave.terminate()
        except AttributeError:
            pass

        try:
            self.master.terminate()
        except AttributeError:
            pass

        if exit_:
            self._stop_queue()

    @staticmethod
    def get(name):
        "return the value of given name from database. Usage: `get <name>`"
        try:
            value = get_realtime_setting(name.upper())
            if value is None:
                raw_print("No record found for `{0}`".format(name))
            else:
                raw_print(value)
        except AttributeError:
            traceback.print_exc()

    @staticmethod
    def set(name, *options):
        "set the value of given name to database. Usage: `set <name> <value>`"
        value = "".join([str(option) for option in options])
        try:
            set_realtime_setting(name.upper(), value)
        except (AttributeError, ValueError):
            traceback.print_exc()

    @staticmethod
    def _clean_log_file():
        open(settings.FILENAME, 'w').close()

    @staticmethod
    def _clean_downloads():
        # Clear the downloaded media
        try:
            logger.debug("Clearing the media")
            shutil.rmtree(settings.DOWNLOADS, ignore_errors=True)
        except FileNotFoundError:
            pass
        os.makedirs(settings.DOWNLOADS, exist_ok=True)


    @staticmethod
    def _clean_shared():
        try:
            logger.debug("Clearing the shared media")
            shutil.rmtree(settings.SHARED, ignore_errors=True)
        except FileNotFoundError:
            pass

        os.makedirs(settings.SHARED, exist_ok=True)

    @staticmethod
    def _clean_db_file():
        # Clean the database. This operation is not suggested.
        raw_print("Deleting database may cause trouble. Are you sure?[y/N]: ", end="")
        if input() == 'y':
            open(settings.DB_NAME, 'w').close()

    def clear(self, *options):
        "clears the log file. Usage: `clear <log/downloads/shared/all>`"

        if not options:
            raise TypeError

        for option in options:
            if option in ("log", "all"):
                self._clean_log_file()
            if option in ("downloads", "all"):
                self._clean_downloads()
            if option in ("shared", "all"):
                self._clean_shared()
            if option in ("db",):
                self._clean_db_file()

    clean = clear

    def reload(self, *_):
        "reload the program"
        self.stop()
        self.start()

    def hardreload(self, *_):
        "reload the program with termination"
        self.terminate(exit_=False)
        self.start()

    def _print_help(self, function_string, printed_helps):
        function = getattr(self, function_string)
        if printed_helps and function in printed_helps:
            # Sometimes different functions does the same
            # operation. No need to print them
            return
        printed_helps.append(function)
        docstring = function.__doc__
        name = function.__name__
        raw_print("\t{0:15}: {1}".format(name, docstring))

    def help(self, option=None):
        "show the help"
        if option is None:
            printed_helps = []
            for function in sorted(self.__callables__):
                self._print_help(function, printed_helps)
        else:
            self._print_help(option, [])

    def __bool__(self):
        return self.is_active
