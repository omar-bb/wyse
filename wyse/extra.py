import requests
import time
import sys


def get_url(url, headers=None):
    r = requests.get(url, headers=headers)
    r.raise_for_status()

    return r


def loading_animation(animation, message, c):
    print(f"\r{message} {animation[c % len(animation)]}", end="")
    time.sleep(0.1)
