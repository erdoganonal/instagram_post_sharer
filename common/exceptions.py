"""
    All custom exceptions that migth be
    raise from the application
"""
import json


class BaseAPIException(Exception):
    "Base of all below exceptions"


class LoginFail(BaseAPIException):
    "raises when login failed"

    def __init__(self):
        super().__init__("Login failed!")


class NoSuchUser(BaseAPIException):
    "raises when given id matches no user id"

    def __init__(self, idx):
        super().__init__(
            f"No such user with id: {idx}"
        )


class AlreadyLocked(BaseAPIException):
    "raises when given path is already locked"

    def __init__(self, path):
        super().__init__(
            f"The path [{path}] already locked."
        )


class WaitAFewMinutes(BaseAPIException):
    "Raises when server returned with wait message"


class AuthorizionError(BaseAPIException):
    "Raises when auhorization error comes from server"


class UnknownFailMessage(BaseAPIException):
    "Raises when error has message but not handled"


class UnknownFail(BaseAPIException):
    "Raises when error has no message"

    def __init__(self, json_value):
        super().__init__(json.dumps(json_value))


class UnknownMediaExtension(BaseAPIException):
    "Raises when given extension is not valid"

    def __init__(self, name):
        super().__init__(
            ".{0} is not a valid media type"
            "".format(name.split('.')[-1])
        )


class UnknownMediaType(BaseAPIException):
    "Raises when given media type is not valid"
