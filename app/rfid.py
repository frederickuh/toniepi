from mfrc522 import SimpleMFRC522
import threading
import time

reader = SimpleMFRC522()

_last_uid = None
_lock = threading.Lock()

def poll_rfid():
    global _last_uid
    while True:
        uid, _ = reader.read_no_block()
        if uid:
            with _lock:
                _last_uid = str(uid)
        time.sleep(0.2)

def get_last_uid():
    with _lock:
        return _last_uid

def clear_last_uid():
    global _last_uid
    with _lock:
        _last_uid = None