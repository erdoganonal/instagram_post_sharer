"""
A instagram user for getting
popular medias. Those medias will be
post in the other account.
"""
import os
import time
import calendar
import urllib
import shutil

from instagram.duplicate import is_any_photo_shared
from instagram.base import BaseInstagram, MediaTypes
import settings
from common import exceptions
from common.tools import LockDir, raise_exception_by_message
from common.logger import logger
from instagram_database.db import User, DB, get_realtime_setting
from OCR.ocr import convert_jpg_to_text


class SlaveInstagram(BaseInstagram):
    "Slave instagram user"

    def __init__(self, username, password, queue=None, **kwargs):
        super().__init__(username, password, queue, **kwargs)
        self._db = DB()
        self._users = []

    @property
    def users(self):
        "Returns the users"
        return self._users

    def _start(self):
        cycle = get_realtime_setting('LOAD_EVERY_X_CYCLE', int)
        while self.is_active:
            wait_time_s = get_realtime_setting('WAIT_TIME_S', int)
            if cycle >= get_realtime_setting('LOAD_EVERY_X_CYCLE', int):
                logger.info("Updating")
                self.load()
                cycle = 0

            logger.info("Retreiving medias...")
            for user in self.users:
                posts = self.get_posts(user.id, wait_time_s, post_count=-1)
                if posts is None:
                    # Something went wrong
                    continue

                logger.info("Downloading posts for user %s", user.name)
                self.download_images(user.name, posts)
            cycle += 1

            self._wait_with_log("WAIT_TIME_S")

    def _update_database(self):
        self.getSelfUsersFollowing()
        followings = self.LastJson["users"].copy()

        self._clear_unfollowed_users(followings)

        for user in followings:
            self.searchUsername(user["username"])
            user = self.LastJson["user"]

            mean_like_count, mean_comment_count = self.get_user_info(
                user["pk"], check_on=100)

            user_in_db = User(
                user["pk"],
                user["username"],
                calendar.timegm(time.gmtime()),
                user["follower_count"],
                mean_like_count,
                mean_comment_count,
                "General"
            )
            is_user_exists = len(
                self._db.select(User, User.id == user_in_db.id)
            ) == 1

            if is_user_exists:
                self._db.update(user_in_db)
            else:
                self._db.insert(user_in_db)
        logger.debug("Database updated")

    def _clear_unfollowed_users(self, followings):
        followings = [user["pk"] for user in followings]
        for user in self._db.select(User):
            if user.id not in followings:
                self._db.delete(user)

    def get_user_info(self, user_id, check_on=100):
        "Returns the basic user information"
        self.getUserFeed(user_id)
        try:
            media = self.LastJson["items"].copy()
        except KeyError as error:
            raise_exception_by_message(self.LastJson, error)

        if not media:
            return 0, 0

        total_likes = 0
        total_comments = 0
        index = 0
        for index, item in enumerate(media):
            if index == check_on:
                break
            total_likes += item["like_count"]
            try:
                total_comments += item["comment_count"]
            except KeyError:
                # Comments are disabled
                pass

        return int(total_likes / index), int(total_comments / index)

    def load(self):
        "Loads database and the users"
        self._update_database()
        self._users = self._db.select(User)
        logger.debug(
            "Users are: %s",
            ' '.join([str(user) for user in self._users])
        )

    def get_user_by_id(self, user_id):
        "Returns the user which saved in the database"
        for user in self.users:
            if user.id == user_id:
                return user
        raise exceptions.NoSuchUser(user_id)

    def get_posts(self, user_id, wait_time_s, post_count=-1):
        "Gets the post for given user"
        # Set how much time we go back
        min_timestamp = calendar.timegm(time.gmtime()) - (wait_time_s * 2)
        self.getUserFeed(user_id, minTimestamp=min_timestamp)
        # Copy the response in case of changes
        try:
            media = self.LastJson["items"].copy()
        except KeyError as error:
            raise_exception_by_message(self.LastJson, error)

        return self.get_media_urls(
            media, post_count,
            max_timestamp=min_timestamp + wait_time_s,
        )

    @staticmethod
    def _get_url(item):
        try:
            return item["video_versions"][0]["url"], MediaTypes.VIDEO
        except KeyError:
            return item["image_versions2"]["candidates"][0]["url"], MediaTypes.PHOTO

    def _is_media_filtered(self, item, **filters):
        max_timestamp = filters.pop("max_timestamp")
        logger.debug(
            "Media taken at %s, max_timestamp is %s",
            time.strftime('%Y-%m-%d %H:%M:%S',
                          time.localtime(item["taken_at"])),
            time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(max_timestamp))
        )
        if item["taken_at"] > max_timestamp:
            logger.debug("The media will be filtered on max_timestamp")
            return True

        user = self.get_user_by_id(item["user"]["pk"])
        try:
            logger.debug(
                "Media has %d comments, avarage comment count is %d",
                item["comment_count"], user.mean_comment_count
            )
            if item["comment_count"] < user.mean_comment_count:
                logger.debug("The media will be filtered on comment count")
                return True
        except KeyError:
            pass

        logger.debug(
            "Media has %d likes, avarage like count is %d",
            item["like_count"], user.mean_like_count
        )
        if item["like_count"] < user.mean_like_count:
            logger.debug("The media will be filtered on like count")
            return True

        return False

    def get_media_urls(self, media, post_count, **filters):
        "Yields the urls for given media"
        try:
            if post_count <= 0:
                # A little trick to prevent code duplication
                raise TypeError
        except TypeError:
            post_count = len(media)

        for index, item in enumerate(media):
            if index == post_count:
                break

            key = str(item["pk"])
            if self._is_media_filtered(item, **filters):
                post_count += 1
                continue
            urls = {key: []}
            try:
                urls[key].append(self._get_url(item))
            except KeyError:
                for carousel_media in item["carousel_media"]:
                    urls[key].append(self._get_url(carousel_media))
            yield urls

    @staticmethod
    def download_image(url, path, filename):
        "Downloads the image"
        try:
            urllib.request.urlretrieve(url, filename=filename)
        except urllib.error.URLError:
            # If download fails, skip others and clean
            os.chdir(settings.BASE_DIR)
            shutil.rmtree(path)
            return None

        text_in_image = convert_jpg_to_text(
            os.path.join(path, filename),
            'TURKISH'
        )
        if text_in_image.strip():
            logger.warning("The text of the image is: %s", text_in_image)
        return text_in_image

    def download_images(self, username, media_urls):
        "Downloads the images from given url list"
        downloaded_media_count = 0
        is_shared_before = False
        for item in media_urls:
            key = list(item)[0]
            urls = item[key]

            path = os.path.join(settings.DOWNLOADS, f"downloaded_images_{key}")

            os.makedirs(path, exist_ok=True)
            with LockDir(path):
                os.chdir(path)

                for index, (url, media_type) in enumerate(urls):
                    filename = f"{index}_{key}_{username}{MediaTypes.get_extension(media_type)}"

                    text_in_image = self.download_image(url, path, filename)
                    if text_in_image is None:
                        # Failed to download image
                        logger.error("Image download failed.")
                        continue

                    downloaded_media_count += 1

            if is_any_photo_shared(path):
                logger.warning(
                    "The image shared before, filtered on image"
                )
                is_shared_before = True

            os.chdir(settings.BASE_DIR)
            if is_shared_before:
                for _ in range(10):
                    try:
                        shutil.rmtree(path)
                    except PermissionError:
                        time.sleep(0.5)
                    else:
                        break

        logger.info("%s media has been downloaded.", downloaded_media_count)

    def send_request(self, endpoint, post=None, login=False):
        "Sends the request to the endpoint"
        self.SendRequest(endpoint, post, login)

        return self.LastJson, self.LastResponse
