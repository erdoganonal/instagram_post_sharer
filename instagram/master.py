"""
A instagram user for posting medias.
"""
import os
import time
import glob
import shutil

import settings
from instagram.base import BaseInstagram
from common.tools import LockDir
from common.logger import logger
from instagram_database.db import get_realtime_setting


class MasterInstagram(BaseInstagram):
    "Master instagram user"

    def _start(self):
        # threading.Thread(target=self._start_cleaner).start()
        self._start_sharing()

    def _start_cleaner(self):
        pass

    def _start_sharing(self):
        os.makedirs(settings.DOWNLOADS, exist_ok=True)
        os.makedirs(settings.SHARED, exist_ok=True)
        logger.info("Listening the downloads folder")
        while self.is_active:
            logger.debug("Checking downloads folder")
            for downloads in os.listdir(settings.DOWNLOADS):
                downloads = os.path.join(settings.DOWNLOADS, downloads)
                self.share_from_folder(downloads)
            logger.debug("Downloads folder check is done.")
            time.sleep(
                get_realtime_setting("LISTENER_WAIT_TIME", int, 60)
            )

    def share_from_folder(self, downloads):
        "Shares file in the given folder"
        os.chdir(downloads)
        logger.info("New folder %s found.", downloads)
        with LockDir(downloads, wait_until_release=True):
            to_shared = []
            for file in glob.glob(f"*jpg"):
                to_shared.append(file)
            self.share(to_shared)

        os.chdir(settings.BASE_DIR)
        self.move_to_shared(downloads)

    def share(self, share_list):
        "Shares the given files"
        if len(share_list) == 1:
            self._share_single(share_list[0])
        elif share_list:
            self._share_carousel(share_list)
        else:
            # Empty folder
            return

    def _share_single(self, filename):
        self.uploadPhoto(filename)

    def _share_carousel(self, carousel_media):
        album = []
        for media in carousel_media:
            album.append({
                "file": media,
                "type": "photo"
            })
        self.uploadAlbum(album)

    @staticmethod
    def move_to_shared(path):
        "Moves the downloaded file under shared folder and renames"
        basename = os.path.basename(path)
        basename = basename.replace("downloaded", "shared")
        shutil.move(path, os.path.join(settings.SHARED, basename))
