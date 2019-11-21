"""
A instagram user base
"""
import time
import json
import math
import copy

from requests_toolbelt import MultipartEncoder
from moviepy.editor import VideoFileClip
from InstagramAPI import InstagramAPI

from common.logger import logger
from common import exceptions

from instagram_database.db import get_realtime_setting

MEDIA_TYPE_PHOTO_EXT = ".jpg"
MEDIA_TYPE_VIDEO_EXT = ".mp4"


class MediaTypes:
    "Types of the media"
    PHOTO = 1
    VIDEO = 2
    CAROUSEL = 8

    @classmethod
    def get_media_type(cls, name, ignore_error=False):
        "Returns the type of the media"
        if name.endswith(MEDIA_TYPE_PHOTO_EXT):
            return cls.PHOTO
        if name.endswith(MEDIA_TYPE_VIDEO_EXT):
            return cls.VIDEO

        if ignore_error:
            return None

        raise exceptions.UnknownMediaExtension(name)

    @classmethod
    def get_extension(cls, media_type, ignore_error=False):
        "Returns the extension of known media type"
        if media_type == cls.PHOTO:
            return MEDIA_TYPE_PHOTO_EXT
        if media_type == cls.VIDEO:
            return MEDIA_TYPE_VIDEO_EXT

        if ignore_error:
            return None

        raise exceptions.UnknownMediaType(media_type)

    @classmethod
    def is_type_of(cls, name, type_):
        "Checks the type of the name"
        return type_ == cls.get_media_type(name)

    @classmethod
    def is_known_extension(cls, name):
        "Return True if given name has known extension"
        return name.endswith((MEDIA_TYPE_PHOTO_EXT, MEDIA_TYPE_VIDEO_EXT))


class BaseInstagram(InstagramAPI):
    "Base for instagram user"

    def __init__(self, username, password, queue=None, **kwargs):
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
                spin_count = (wait_time_s - total_waited_time) // wait_secs
                seconds = wait_time_s
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

    def delete_all_media(self):
        "Deletes entire posts of logined user"
        self.getSelfUserFeed()
        for post in self.LastJson["items"]:
            self.deleteMedia(post["id"])

    def upload_video(self, video, thumbnail, **kwargs):
        "Uploads the given video on instagram"
        if kwargs.pop("upload_id", None) is None:
            upload_id = str(int(time.time() * 1000))
        data = {'upload_id': upload_id,
                '_csrftoken': self.token,
                'media_type': '2',
                '_uuid': self.uuid}
        if kwargs.pop("is_sidecar", None):
            data['is_sidecar'] = '1'
        multipart_encoder = MultipartEncoder(data, boundary=self.uuid)
        self.s.headers.update({'X-IG-Capabilities': '3Q4=',
                               'X-IG-Connection-Type': 'WIFI',
                               'Host': 'i.instagram.com',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'Accept-Encoding': 'gzip, deflate',
                               'Content-type': multipart_encoder.content_type,
                               'Connection': 'keep-alive',
                               'User-Agent': self.USER_AGENT})
        response = self.s.post(
            self.API_URL + "upload/video/", data=multipart_encoder.to_string()
        )
        if response.status_code == 200:
            self._upload_video(
                video, thumbnail, upload_id, json.loads(response.text), **kwargs
            )

    # pylint: disable=too-many-locals
    def _upload_video(self, video, thumbnail, upload_id, body, **kwargs):
        upload_url = body['video_upload_urls'][3]['url']
        upload_job = body['video_upload_urls'][3]['job']

        video_data = open(video, 'rb').read()
        request_size = int(math.floor(len(video_data) / 4))
        last_request_extra = (len(video_data) - (request_size * 3))

        headers = copy.deepcopy(self.s.headers)
        self.s.headers.update({'X-IG-Capabilities': '3Q4=',
                               'X-IG-Connection-Type': 'WIFI',
                               'Cookie2': '$Version=1',
                               'Accept-Language': 'en-US',
                               'Accept-Encoding': 'gzip, deflate',
                               'Content-type': 'application/octet-stream',
                               'Session-ID': upload_id,
                               'Connection': 'keep-alive',
                               'Content-Disposition': 'attachment; filename="video.mov"',
                               'job': upload_job,
                               'Host': 'upload.instagram.com',
                               'User-Agent': self.USER_AGENT})
        for i in range(0, 4):
            start = i * request_size
            if i == 3:
                end = i * request_size + last_request_extra
                length = last_request_extra
            else:
                end = (i + 1) * request_size
                length = request_size
            content_range = "bytes {start}-{end}/{video_length}".format(
                start=start, end=(end - 1), video_length=len(video_data)
            ).encode('utf-8')

            self.s.headers.update({
                'Content-Length': str(end - start), 'Content-Range': content_range,
            })
            response = self.s.post(
                upload_url,
                data=video_data[start:start + length]
            )
        self.s.headers = headers

        if response.status_code == 200:
            # Wait 60 seconds to to be finised the transcode
            time.sleep(60)
            if self.configure_video(upload_id, video, thumbnail, **kwargs):
                return self.expose()
        return False

    def configure_video(self, upload_id, video, thumbnail, **kwargs):
        "Prepares video before expose"
        clip = VideoFileClip(video)
        caption = kwargs.pop("caption", '')
        self.uploadPhoto(photo=thumbnail, caption=caption, upload_id=upload_id)
        data = json.dumps({
            'upload_id': upload_id,
            'source_type': 3,
            'poster_frame_index': 0,
            'length': 0.00,
            'audio_muted': False,
            'filter_type': 0,
            'video_result': 'deprecated',
            'clips': {
                'length': clip.duration,
                'source_type': '3',
                'camera_position': 'back',
            },
            'extra': {
                'source_width': clip.size[0],
                'source_height': clip.size[1],
            },
            'device': self.DEVICE_SETTINTS,
            '_csrftoken': self.token,
            '_uuid': self.uuid,
            '_uid': self.username_id,
            'caption': caption,
        })
        clip.reader.close()
        clip.audio.reader.close_proc()
        return self.SendRequest('media/configure/?video=1', self.generateSignature(data))

    def _start(self):
        raise NotImplementedError

    def __del__(self):
        self.stop()
