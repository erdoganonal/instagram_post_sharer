"General settings for entire application"
import os
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database settings
DB_NAME = "instagram_post_share.db"

# Slave Instagram settings
SLAVE_USERNAME = "XXXX"
SLAVE_PASSWORD = "XXXX"

# Master Instagram settings
MASTER_USERNAME = "XXXX"
MASTER_PASSWORD = "XXXX"

# Paths
DOWNLOADS = os.path.join(BASE_DIR, "downloads")
SHARED = os.path.join(BASE_DIR, "shared")

# Times
WAIT_TIME_S = 60 * 60  # Seconds
LOAD_EVERY_X_CYCLE = 12
WAIT_SECS = 10
LISTENER_WAIT_TIME = 60  # Seconds

# Logging
LOGGER_NAME = "instagram_post_share"
LOG_LEVEL = logging.DEBUG
FILENAME = "instagram_post_share_app.log"
FORMAT = "%(levelname)s:%(processName)s:%(filename)s:%(funcName)s:%(lineno)d:: %(message)s"

# Proxy
DEFAULT_PROXY = "XXXX"
