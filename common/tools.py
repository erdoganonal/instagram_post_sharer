"Common tools for the application."
import sys
import os
import time
import tempfile
import logging
import urllib
from multiprocessing import Queue
from pyreadline import Readline

import settings
from common import exceptions
from common.logger import logger
from instagram_database.db import get_realtime_setting

# Redirect whole output to stdout
sys.stdout = open(os.devnull, 'w')


class _Completer:  # Custom completer

    def __init__(self, *options):
        self.options = []
        self.matches = None
        self.add_options(*options)

    def complete(self, text, state):
        "complater function for auto-complation"
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state] + ' '
        except IndexError:
            return None

    def add_options(self, *options):
        "Add options for auto-complate"
        for option in options:
            self.options.append(option)
        self.options = sorted(self.options)


COMPLATER = _Completer()

_READLINE = Readline()
_READLINE.ctrl_c_timeout = 0
_READLINE.set_completer(COMPLATER.complete)
_READLINE.parse_and_bind('tab: complete')


def autocomplate_input(message=''):
    "input-lke function with auto-complate"
    sys.stdout = sys.__stdout__
    input_ = _READLINE.readline(message).strip('\n')
    sys.stdout = open(os.devnull, 'w')
    return input_


class QQ:
    "A simple Queue for storing the system state"

    def __init__(self):
        self._queue = Queue()
        self._queue.put(True)

    @property
    def state(self):
        "Returns the state of the system from give Queue"
        state = self._queue.get()
        self._queue.put(state)
        self.state = state
        return state

    @state.setter
    def state(self, state):
        while not self._queue.empty():
            self._queue.get()
        self._queue.put(state)

    @property
    def queue(self):
        "Returns the Queue instance"
        return self._queue


Q = QQ()


def raw_print(*args, sep=' ', end='\n', flush=True):
    "stdout redirected to nul due to unnecessary prints from external library"
    message = sep.join(str(arg) for arg in args) + end
    sys.__stdout__.write(message)
    if flush:
        sys.__stdout__.flush()


def set_proxy(obj, proxy=settings.DEFAULT_PROXY):
    "Sets the proxy"
    try:
        urllib.request.urlopen("http://www.google.com", timeout=1)
    except urllib.error.URLError:
        logger.warning("Setting proxy")
        obj.setProxy(proxy)
    else:
        return

    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    proxy_support = urllib.request.ProxyHandler(proxies)
    opener = urllib.request.build_opener(
        proxy_support,
        urllib.request.HTTPBasicAuthHandler(),
        urllib.request.CacheFTPHandler
    )

    urllib.request.install_opener(opener)


def log_level_checker(queue):
    "Listens LOG_LEVEL at realtime from database. On change, sets."
    while queue.state:
        log_level_old = logger.level
        log_level_new = get_realtime_setting("LOG_LEVEL", int)

        if log_level_old != log_level_new:
            logger.setLevel(log_level_new)
            logger.warning(
                "Log level has been changed from %s to %s",
                logging.getLevelName(log_level_old),
                logging.getLevelName(log_level_new)
            )
        # Check evert X seconds
        time.sleep(5)


def raise_exception_by_message(json, error):
    "Raises exception based on message"
    logger.error("Actual error is: %s", error)
    logger.error("Incoming data is: %s", json)
    try:
        message = json["message"]
        if message == "Not authorized to view user":
            raise exceptions.AuthorizionError(message)
        if message == "Please wait a few minutes before you try again.":
            raise exceptions.WaitAFewMinutes(message)

        raise exceptions.UnknownFailMessage(message)
    except KeyError:
        raise exceptions.UnknownFail(json)


class LockDir():
    "Locks the directory"
    _LOCK_FILE = ".locked.lock"

    def __init__(self, path, wait_until_release=False):
        self.path = path
        self.wait_until_release = wait_until_release
        self._lock_file = os.path.join(path, self._LOCK_FILE)

    @property
    def lock_file(self):
        "Returns the lock file"
        return self._lock_file

    @property
    def is_locked(self):
        "Returns the directorylock state"
        return os.path.isfile(self.lock_file)

    def _lock(self):
        open(self.lock_file, 'w').close()

    def lock(self):
        "Acuires the lock"
        while True:
            if self.is_locked:
                if self.wait_until_release:
                    time.sleep(0.5)
                else:
                    raise exceptions.AlreadyLocked(self.path)
            else:
                self._lock()
                break

    def release(self):
        "Releases the directory"
        try:
            os.unlink(self.lock_file)
        except FileNotFoundError:
            # Already unlocked
            pass

    def __enter__(self):
        self.lock()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.release()


class Lock(LockDir):
    "acquires the lock for current process"
    _LOCK_FILE = ".post_sharer_lock_file.lock"

    def __init__(self):
        super().__init__(tempfile.gettempdir())
