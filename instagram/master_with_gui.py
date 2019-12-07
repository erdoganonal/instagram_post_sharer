"""
A instagram user for posting medias. Uses the browser.
"""
import os
import shutil
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common import exceptions as selenium_exp
from selenium.webdriver.chrome.options import Options

import settings
from common.tools import LockDir
from common.logger import logger
from common.exceptions import LoginFail
from instagram.base import BaseInstagram, MediaTypes

URL = "https://www.instagram.com/accounts/login/?source=auth_switcher"


class MasterInstagram(BaseInstagram):
    "Master instagram user with GUI"

    def __init__(self, username, password, queue=None):
        self.username = username
        self.password = password
        self.browser = self._get_browser()

        super().__init__(username, password, queue)

    def _find_element_by_text(
            self,
            by_element, filter_on, text,
            *args,
            timeout=5,
            on_error=None,
            action=None, call=False,
            **kwargs):
        start_time = time.time()
        while time.time() - start_time <= timeout:
            elements = self.browser.find_elements(by_element, filter_on)
            for element in elements:
                try:
                    if element.text == text and action:
                        callable_ = getattr(element, action)
                        if call:
                            return callable_(*args, **kwargs)
                        return callable_
                    if element.text == text:
                        return element
                except selenium_exp.StaleElementReferenceException:
                    continue
        if isinstance(on_error, BaseException):
            raise on_error
        return on_error

    def login(self, force=False):
        "Login to instagram"
        WebDriverWait(self.browser, 10).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        username_input = self.browser.find_element_by_name("username")
        username_input.send_keys(self.username)

        password_input = self.browser.find_element_by_name("password")
        password_input.send_keys(self.password)

        self._find_element_by_text(
            By.TAG_NAME,
            "button",
            "Log In",
            action="click",
            call=True,
            on_error=LoginFail
        )

        self._skip_popups()

    def _skip_popups(self, timeout=5):
        # close Trun on Notifications pop-up, if exists
        for button in ("Not Now", "Cancel",):
            self._find_element_by_text(
                By.TAG_NAME,
                "button",
                button,
                action="click",
                call=True,
                on_error=None,
                timeout=timeout
            )

    @staticmethod
    def _get_browser():
        options = Options()

        if settings.HEADLESS:
            options.add_argument("--headless")  # Runs Chrome in headless mode.
        options.add_argument('start-maximized')
        options.add_argument('disable-infobars')
        options.add_experimental_option(
            "mobileEmulation", {"deviceName": "Nexus 5"})
        # options.add_argument("--disable-extensions")

        browser = webdriver.Chrome(
            options=options,
            executable_path=settings.CHROME_DRIVER
        )

        browser.get(URL)

        return browser

    def start(self):
        "Starts the program"
        self.login()
        self._start()

    def _start(self):
        # threading.Thread(target=self._start_cleaner).start()
        self._start_sharing()

    def _start_cleaner(self):
        pass

    def _locate_share_button(self, click=True):
        spans = self.browser.find_elements_by_tag_name("span")
        for span in spans:
            if span.get_attribute("aria-label") == "New Post":
                if click:
                    span.click()
                return span

        return None

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

            self._wait_with_log("LISTENER_WAIT_TIME")

    def share_from_folder(self, downloads):
        "Shares file in the given folder"
        os.chdir(downloads)
        logger.info("New folder %s found.", downloads)
        with LockDir(downloads, wait_until_release=True):
            to_shared = [file for file in os.listdir(".")
                         if MediaTypes.is_known_extension(file)]

            try:
                self.share(to_shared)
            except NotImplementedError:
                pass

        os.chdir(settings.BASE_DIR)
        self.move_to_shared(downloads)

    def share(self, share_list):
        "Shares the given files"

        if len(share_list) == 1:
            self._share_single(share_list[0])
        elif share_list:
            raise NotImplementedError
            # self._share_carousel(share_list)
        else:
            # Empty folder
            return

    def _share_single(self, filename):
        media_type = MediaTypes.get_media_type(filename, ignore_error=True)

        if media_type == MediaTypes.PHOTO:
            self.upload_photo(filename)
        elif media_type == MediaTypes.VIDEO:
            raise NotImplementedError
            # self.upload_video(filename, settings.DEFAULT_THUMBNAIL)
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

    def upload_photo(self, filename):
        "Uploads photo"
        self._locate_share_button(click=True)

        time.sleep(1)

        share_input = self.browser.find_elements_by_tag_name("input")[3]
        share_input.send_keys(os.path.join(os.getcwd(), filename))

        for button_text in ("Next", "Share"):
            self._find_element_by_text(
                By.TAG_NAME, "button",
                button_text,
                action="click", call=True
            )

        self._skip_popups(timeout=5)

    @staticmethod
    def move_to_shared(path):
        "Moves the downloaded file under shared folder and renames"
        basename = os.path.basename(path)
        basename = basename.replace("downloaded", "shared")
        shutil.move(path, os.path.join(settings.SHARED, basename))
