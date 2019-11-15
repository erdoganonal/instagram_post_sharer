"Common tools for the application."
import sys
import os
import time
import shutil
import logging
import urllib
from multiprocessing import Queue

import settings
from common import exceptions
from common.logger import logger
from instagram_database.db import get_realtime_setting

# Redirect whole output to stdout
sys.stdout = open(os.devnull, 'w')


class QQ:
    "A simple Queue for storing the system state"

    def __init__(self):
        self._queue = Queue()

    @property
    def state(self):
        "Returns the state of the system from give Queue"
        state = self._queue.get()
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


def clean():
    "Clears the downloads"
    # Clear the whole media
    try:
        logger.debug("Clearing the media")
        shutil.rmtree(settings.DOWNLOADS, ignore_errors=True)
    except FileNotFoundError:
        pass
    os.makedirs(settings.DOWNLOADS, exist_ok=True)
    # Clean the log file
    open(settings.FILENAME, 'w').close()


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
