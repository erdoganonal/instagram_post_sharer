
"This is where the program starts."
import sys

import imageio

from common.controller import start_app

try:
    imageio.plugins.ffmpeg.get_exe()
except imageio.core.fetching.NeedDownloadError:
    sys.stderr.write("Failed to import video upload library.\n")
    sys.stderr.write("Downloading the executable. Please wait...\n")
    imageio.plugins.ffmpeg.download()
    sys.stderr.write("\nDownload has been completed. Program should be restarted.\n")
    sys.exit("Exiting...")


def main():
    "Starts the program"
    start_app()


if __name__ == "__main__":
    main()
