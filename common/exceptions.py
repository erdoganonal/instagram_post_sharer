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
    "Raises when server returned with wait message"


class UnknownFailMessage(BaseAPIException):
    "Raises when server returned with wait message"


class UnknownFail(BaseAPIException):
    "Raises when server returned with wait message"

    def __init__(self, json_value):
        super().__init__(json.dumps(json_value))
