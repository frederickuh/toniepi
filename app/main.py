import time
import signal
import sys

from rfid import read_tag
from audio import play, stop
from storage import get_tag_map
from leds import idle, playing

current_uid = None

def cleanup(sig=None, frame=None):
    stop()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

idle()

while True:
    uid = read_tag()

    if uid:
        if uid != current_uid:
            tag_map = get_tag_map()
            if str(uid) in tag_map:
                play(uid, tag_map[str(uid)])
                playing()
            current_uid = uid
    else:
        if current_uid:
            stop()
            idle()
            current_uid = None

    time.sleep(0.3)