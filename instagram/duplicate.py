"Gives some tools for checking the image is shared before"
import os
import logging

from cv2 import cv2

from settings import SHARED
from common.tools import logger

TRESHOLD = 0.3
TRESHOLD_PERCANTAGE = 90


def is_similar(image1, image2):
    "Compares two images"
    logger.debug(
        "First image: %s, Second image: %s", image1, image2
    )
    image1 = cv2.imread(image1)
    image2 = cv2.imread(image2)

    first_image_hist = cv2.calcHist([image1], [0], None, [256], [0, 256])
    second_image_hist = cv2.calcHist([image2], [0], None, [256], [0, 256])

    # img_hist_diff = cv2.compareHist(
    #     first_image_hist, second_image_hist,
    #     cv2.HISTCMP_BHATTACHARYYA
    # )
    img_template_probability_match = cv2.matchTemplate(
        first_image_hist, second_image_hist,
        cv2.TM_CCOEFF_NORMED
    )[0][0]

    img_template_probability_match *= 100
    similar = bool(img_template_probability_match >= TRESHOLD_PERCANTAGE)

    log_level = logging.WARNING if similar else logging.INFO

    logger.log(
        log_level,
        "Similarity: %s",
        str(img_template_probability_match)
    )

    return similar


def is_shared(filepath):
    "Checks the file to decide the image shared before or not"
    for folder in os.listdir(SHARED):
        folder = os.path.join(SHARED, folder)
        logger.info("folders are: %s", folder)
        for filename in os.listdir(folder):
            filename = os.path.join(folder, filename)
            if is_similar(filepath, filename):
                return True
    return False


def is_any_photo_shared(folder):
    "Checks the files in the folder to decide the image shared before or not"
    logger.info("Checking for is any photo shared before")
    for filename in os.listdir(folder):
        logger.debug("Filename is: %s", filename)
        if is_shared(os.path.join(folder, filename)):
            return True
    return False
