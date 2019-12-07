"""
Does the some checks for program
"""
import sys
import os
import urllib
import imageio

import settings


def check_ffmpeg_exe():
    "check the video upload executable"
    if settings.MASTER_WITH_GUI:
        # In GUI mode, no need execuable
        return
    try:
        imageio.plugins.ffmpeg.get_exe()
    except imageio.core.fetching.NeedDownloadError:
        sys.stderr.write("Failed to import video upload library.\n")
        sys.stderr.write("Downloading the executable. Please wait...\n")
        imageio.plugins.ffmpeg.download()
        sys.stderr.write(
            "\nDownload has been completed. Program should be restarted.\n"
        )
        sys.exit("Exiting...")


def check_chrome_driver():
    "check the driver exist or not"
    if settings.MASTER_WITH_GUI and not os.path.isfile(settings.CHROME_DRIVER):
        sys.stderr.write("Failed to locate chromedriver.\n")
        sys.stderr.write("Please locate the driver under base path ")
        sys.stderr.write("or define it's path in settings.py\n")
        sys.exit("Exiting...")


def check_settings():
    if settings.SLAVE_USERNAME is None:
        sys.stderr.write("Username of slave not defined.\n")
        sys.exit()
    if settings.SLAVE_PASSWORD is None:
        sys.stderr.write("Password of slave not defined.\n")
        sys.exit()
    if settings.MASTER_USERNAME is None:
        sys.stderr.write("Username of master not defined.\n")
        sys.exit()
    if settings.MASTER_PASSWORD is None:
        sys.stderr.write("Password of master not defined.\n")
        sys.exit()

    try:
        urllib.request.urlopen("http://www.google.com", timeout=5)
    except urllib.error.URLError:
        sys.stderr.write("No internet connection. ")
        if settings.DEFAULT_PROXY is None:
            sys.stderr.write("No proxy is set.\n")
            sys.exit()
        sys.__stdout__.write("Proxy is found. Will be set ")
        sys.__stdout__.write("after program runs\n")


def initial_check():
    "do initial checks"
    sys.__stdout__.write("Initial check. Please wait...\n")
    sys.__stdout__.flush()

    check_settings()
    check_ffmpeg_exe()
    check_chrome_driver()

    sys.__stdout__.write("Initial check is done. Everything is well\n")
    sys.__stdout__.flush()
