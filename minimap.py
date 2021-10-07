import re
import time
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import ImageGrab
from playwright.sync_api import sync_playwright

VIEWPORT_SIZE = {"width": 300, "height": 350}
POSITION_COORDINATES = [1652, 19, 1920, 35]

TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

MAP_URL = 'https://www.newworld-map.com/'
MAP_WITH_COORDINATES_URL = 'https://www.newworld-map.com/#/?lat={lat}&lng={lng}'

LAST_COORDINATES = []
MAX_LAST_COORDINATES_TO_REMEMBER = 5

path_to_extension = Path().resolve() / 'ext'
user_data_dir = Path().resolve() / 'user_data_dir'
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def is_close_to_any_of_lasts(lng, lat):
    for olng, olat in LAST_COORDINATES:
        if abs(lng - olng) < 100 and abs(lat - olat) < 100:
            return True


with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_agent="Mozilla/5.0 (Linux; Android 9; Pixel 3 Build/PQ1A.181105.017.A1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4641.0 Mobile Safari/537.36",
        is_mobile=True,
        has_touch=True,
        user_data_dir=user_data_dir,
        executable_path=CHROME_PATH,
        headless=False,
        args=[
            f"--disable-extensions-except={path_to_extension}",
            f"--load-extension={path_to_extension}",
        ],
    )

    page = browser.pages[0]
    page.set_viewport_size(VIEWPORT_SIZE)
    page.goto(MAP_URL)
    page.reload()

    while 1:
        screenshot = ImageGrab.grab(POSITION_COORDINATES)
        mask = cv2.inRange(np.array(screenshot), np.array([100, 100, 100]), np.array([255, 255, 255]))
        maybe_coordinates = pytesseract.image_to_string(mask, config="-c tessedit_char_whitelist=[].,0123456789")
        coordinates = re.findall(r'\[(\d{1,5})[,.]{1,2}\d{1,3}[,.]{1,2}(\d{1,5})[,.]', maybe_coordinates)
        if coordinates:
            lng, lat = int(coordinates[0][0]), int(coordinates[0][1])
            LAST_COORDINATES.append((lng, lat))
            if len(LAST_COORDINATES) <= MAX_LAST_COORDINATES_TO_REMEMBER:
                continue
            LAST_COORDINATES.pop(0)
            if is_close_to_any_of_lasts(lng, lat):
                if LAST_COORDINATES[-1] == LAST_COORDINATES[-2]:
                    continue
                page.goto(url=MAP_WITH_COORDINATES_URL.format(lat=lat, lng=lng))

        time.sleep(1)
