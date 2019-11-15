"""
A instagram user base
"""
import time

from InstagramAPI import InstagramAPI

from common.logger import logger
from common import exceptions

from instagram_database.db import get_realtime_setting


# pylint:disable=too-few-public-methods
class MediaTypes:
    "Types of the media"
    PHOTO = 1
    VIDEO = 2
    CAROUSEL = 8


class BaseInstagram(InstagramAPI):
    "Base for instagram user"

    def __init__(self, username, password, queue, **kwargs):
        super().__init__(username, password, **kwargs)
        self.queue = queue
        self._is_active = False

    @property
    def is_active(self):
        "Returns the status of process"
        if self.queue:
            self._is_active = self.queue.state
        return self._is_active

    def _wait_with_log(self, seconds, update_on):
        "Waits given seconds with a log."
        # Log every `WAIT_SECS` seconds
        wait_secs = get_realtime_setting("WAIT_SECS", int, 10)
        spin_count = seconds // wait_secs
        leap = seconds % wait_secs
        time.sleep(leap)

        total_waited_time = leap
        while spin_count > 0 and self.is_active:
            wait_secs = get_realtime_setting("WAIT_SECS", int, 10)
            remaining_time = spin_count * wait_secs

            logger.debug("Waiting... %d seconds remained.", remaining_time)

            time.sleep(wait_secs)

            total_waited_time += wait_secs
            wait_time_s = get_realtime_setting(update_on, int)

            if wait_time_s != seconds:
                logger.warning("Time has been updated!")
                if total_waited_time >= wait_time_s:
                    break
                seconds = wait_time_s
                spin_count = (wait_time_s - total_waited_time) // wait_secs
                continue

            spin_count -= 1
        logger.debug("Time is up.")

    def start(self):
        "Starts the program"
        # Try to login
        for _ in range(5):
            if self.login():
                logger.info("Login successful")
                break
            time.sleep(0.5)
        else:
            logger.error("Login failed!")
            raise exceptions.LoginFail

        self._is_active = True
        self._start()

    def stop(self):
        "Stops the program"
        self._is_active = False
        if self.queue:
            self.queue.state = False

    def _start(self):
        raise NotImplementedError

    def __del__(self):
        self.stop()
