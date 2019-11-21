"""
A instagram user for posting medias.
"""
import os
import shutil

import settings
from instagram.base import BaseInstagram, MediaTypes
from common.tools import LockDir
from common.logger import logger


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

            self._wait_with_log(60, "LISTENER_WAIT_TIME")

    def share_from_folder(self, downloads):
        "Shares file in the given folder"
        os.chdir(downloads)
        logger.info("New folder %s found.", downloads)
        with LockDir(downloads, wait_until_release=True):
            to_shared = [file for file in os.listdir(".")
                         if MediaTypes.is_known_extension(file)]

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
        media_type = MediaTypes.get_media_type(filename, ignore_error=True)

        if media_type == MediaTypes.PHOTO:
            self.uploadPhoto(filename)
        elif media_type == MediaTypes.VIDEO:
            self.upload_video(filename, settings.DEFAULT_THUMBNAIL)
        else:
            logger.error("Unkown media type: %s", filename)

    def _share_carousel(self, carousel_media):
        album = []
        for media in carousel_media:
            if MediaTypes.is_type_of(media, MediaTypes.PHOTO):
                type_ = "photo"
            else:
                type_ = "video"

            album.append({
                "file": media,
                "type": type_
            })
        self.uploadAlbum(album)

    @staticmethod
    def move_to_shared(path):
        "Moves the downloaded file under shared folder and renames"
        basename = os.path.basename(path)
        basename = basename.replace("downloaded", "shared")
        shutil.move(path, os.path.join(settings.SHARED, basename))
