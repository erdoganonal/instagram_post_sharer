"""
Does the some checks for program
"""
import sys
import os
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


def initial_check():
    "do initial checks"
    sys.__stdout__.write("Initial check. Please wait...\n")
    sys.__stdout__.flush()

    check_ffmpeg_exe()

    check_chrome_driver()

    sys.__stdout__.write("Initial check is done. Everything is well\n")
    sys.__stdout__.flush()
