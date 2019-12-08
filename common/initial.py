"""
Does the some checks for program
"""
import sys
import os
import urllib
import imageio

import settings
from common.colored_print import Colored
from common.tools import Lock


def check_running_instance():
    "check for running instances."
    if Lock().is_locked:
        Colored.print_warning(
            "Another instance already running."
        )
        sys.exit()

def check_ffmpeg_exe():
    "check the video upload executable"
    if settings.MASTER_WITH_GUI:
        # In GUI mode, no need execuable
        return
    try:
        imageio.plugins.ffmpeg.get_exe()
    except imageio.core.fetching.NeedDownloadError:
        Colored.print_error("Failed to import video upload library.")
        Colored.print_warning("Downloading the executable. Please wait...")
        imageio.plugins.ffmpeg.download()
        Colored.print_warning(
            "\nDownload has been completed. Program should be restarted."
        )
        sys.exit("Exiting...")


def check_chrome_driver():
    "check the driver exist or not"
    if settings.MASTER_WITH_GUI and not os.path.isfile(settings.CHROME_DRIVER):
        Colored.print_error("Failed to locate chromedriver.")
        Colored.print_error(
            "Please locate the driver under base path "
            "or define it's path in settings.py"
        )
        sys.exit("Exiting...")


def check_settings():
    "Check the settings"
    if settings.SLAVE_USERNAME is None:
        Colored.print_error("Username of slave not defined.")
        sys.exit()
    if settings.SLAVE_PASSWORD is None:
        Colored.print_error("Password of slave not defined.")
        sys.exit()
    if settings.MASTER_USERNAME is None:
        Colored.print_error("Username of master not defined.")
        sys.exit()
    if settings.MASTER_PASSWORD is None:
        Colored.print_error("Password of master not defined.")
        sys.exit()

    try:
        urllib.request.urlopen("http://www.google.com", timeout=5)
    except urllib.error.URLError:
        Colored.print_error("No internet connection.")
        if settings.DEFAULT_PROXY is None:
            Colored.print_warning("No proxy is set.")
            sys.exit()
        Colored.print_warning("Proxy is found. Will be set after program runs")


def initial_check():
    "do initial checks"
    Colored.print_debug("Initial check. Please wait...")

    check_running_instance()
    check_settings()
    check_ffmpeg_exe()
    check_chrome_driver()

    Colored.print_info("Initial check is done. Everything is well\n")
