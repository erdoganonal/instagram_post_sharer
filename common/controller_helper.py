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
import threading
from multiprocessing import Process, Queue, active_children

import settings
from common.tools import set_proxy, Q, \
    log_level_checker
from common.colored_print import Colored
from common.logger import logger
from instagram.master import MasterInstagram as MasterInstagramWithoutGui
from instagram.master_with_gui import MasterInstagram as MasterInstagramWithGui
from instagram.slave import SlaveInstagram
from instagram_database.db import set_realtime_setting, get_realtime_setting

SLAVE_EXCEPTION_HANDLER = Queue()
MASTER_EXCEPTION_HANDLER = Queue()


if settings.MASTER_WITH_GUI:
    MasterInstagram = MasterInstagramWithGui
else:
    MasterInstagram = MasterInstagramWithoutGui


def start_log_level_checker():
    "gets log level from database and sets on change"
    Q.state = True

    threading.Thread(
        target=log_level_checker,
        args=(Q,),
        name="log_level_listener",
        daemon=True
    ).start()


def module_process_starter(instagram_class, username, password, queue, exception_handler):
    "A function for creating the module in Process"
    instagram = instagram_class(
        username=username,
        password=password,
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
        'hardreload', 'hardrestart',
        'help',
        'start', 'stop',
        'reload', 'restart',
        'terminate', 'exit',
        'status',
    ]

    def __init__(self, queue):
        self.slave = None
        self.master = None
        self.queue = queue
        self.is_active = True

    @property
    def callables(self):
        "return the callables"
        return self.__callables__

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
            if command not in self.callables:
                raise AttributeError
            getattr(self, command)(*options)
        except AttributeError:
            Colored.print_warning(
                "Unknown command. Type help to "
                "see entire commands and it's usages."
            )
        except TypeError:
            Colored.print_warning(
                "Invalid argument. Type help {0} for help".format(command)
            )

    def __call__(self, text):
        "call the related function from string"
        self.call(text)

    def _create_processes(self):
        slave_instagram = Process(
            target=module_process_starter,
            args=(
                SlaveInstagram,
                settings.SLAVE_USERNAME, settings.SLAVE_PASSWORD,
                self.queue, SLAVE_EXCEPTION_HANDLER
            ),
            name="SlaveInstagram",
            daemon=True
        )
        master_instagram = Process(
            target=module_process_starter,
            args=(
                MasterInstagram,
                settings.MASTER_USERNAME, settings.MASTER_PASSWORD,
                self.queue, MASTER_EXCEPTION_HANDLER
            ),
            name="MasterInstagram",
            daemon=True
        )

        return slave_instagram, master_instagram

    def start(self):
        "starts the application. Usage: start"
        self.queue.state = True

        if self.slave and self.slave.is_alive() and self.master and self.master.is_alive():
            Colored.print_warning("Application is already running!")
            return

        self.slave, self.master = self._create_processes()

        logger.debug("Application starting...")
        self.slave.start()
        self.master.start()
        logger.debug("Application started")

    def stop(self):
        "stops the application. Usage: stop"
        self.queue.state = False

        if self.slave:
            self.slave.join()
        if self.master:
            self.master.join()

        start_log_level_checker()
        logger.warning("Application stopped.")

    def exit(self):
        "stop the application and exit. Usage: exit"
        self.stop()
        self._stop_queue()

    def terminate(self, exit_=True):
        "stop the application immediately. Usage: terminate"
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
    def status():
        "print the status of the program. Usage: status"
        active_processes = active_children()
        active_threads = [thread for thread in threading.enumerate()
                          if thread.name != "MainThread" and thread.is_alive()]

        Colored.print_yellow("Active Processes:")
        for active_process in active_processes:
            Colored.print_green("\t{0}".format(active_process.name))

        Colored.print_yellow("Active Threads:")
        for active_thread in active_threads:
            Colored.print_green("\t{0}".format(active_thread.name))

    @staticmethod
    def get(name):
        "return the value of given name from database. Usage: get <name>"
        try:
            value = get_realtime_setting(name.upper())
            if value is None:
                Colored.print_error("No record found for {0}".format(name))
            else:
                Colored.print_green(value)
        except AttributeError:
            exc_info = sys.exc_info()
            Colored.print_error(traceback.format_exception(*exc_info))

    @staticmethod
    def set(name, *options):
        "set the value of given name to database. Usage: set <name> <value>"
        value = "".join([str(option) for option in options])
        try:
            set_realtime_setting(name.upper(), value)
        except AttributeError:
            Colored.print_error("No record found to update.")
        except ValueError:
            Colored.print_error("Could not convert string to float.")
        except ZeroDivisionError:
            Colored.print_error("division by zero")

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
        Colored.print_warning(
            "Deleting database may cause trouble. Are you sure?[y/N]: ",
            end=''
        )
        if input() == 'y':
            open(settings.DB_NAME, 'w').close()

    def clear(self, *options):
        "clears the given output file/folder(s). " \
            "Usage: clear <log/downloads/shared/screen/all>"
        clear_options = ("log", "downloads", "shared", "screen", "all")

        if not options:
            raise TypeError

        for option in options:
            if option not in clear_options:
                Colored.print_error(
                    "\t{0} is not an option for this command".format(option)
                )
                continue

            if option in ("log", "all"):
                self._clean_log_file()
            if option in ("downloads", "all"):
                self._clean_downloads()
            if option in ("shared", "all"):
                self._clean_shared()
            if option in ("screen", "all"):
                os.system("cls")
            if option in ("db",):
                self._clean_db_file()

    clean = clear

    def reload(self):
        "reloads the program. Usage: reload"
        self.stop()
        self.start()

    restart = reload

    def hardreload(self, *_):
        "reload the program with termination. Usage: hardreload"
        self.terminate(exit_=False)
        self.start()

    hardrestart = hardreload

    def _print_help(self, function_string, printed_helps):
        try:
            function = getattr(self, function_string)
        except AttributeError:
            Colored.print_warning(
                "No help found for {0}".format(function_string))
            return
        if printed_helps and function in printed_helps:
            # Sometimes different functions does the same
            # operation. No need to print them
            return
        printed_helps.append(function)
        docstring = function.__doc__
        help_message, usage = docstring.split("Usage: ")
        name = function.__name__
        Colored.print_green(
            "\t{0:15}: {1}\n\t{2}Usage: {3}".format(
                name, help_message, ' ' * 17, usage
            ))

    def help(self, option=None):
        "show the help. Usage: help"
        if option is None:
            printed_helps = []
            for function in sorted(self.callables):
                self._print_help(function, printed_helps)
        else:
            self._print_help(option, [])

    def __bool__(self):
        return self.is_active
