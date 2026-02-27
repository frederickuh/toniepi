import json
import os
from config import POSITION_FILE, TAG_FILE

def _load(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def _save(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

def get_position(uid):
    return _load(POSITION_FILE).get(str(uid), 0)

def save_position(uid, pos):
    data = _load(POSITION_FILE)
    data[str(uid)] = pos
    _save(POSITION_FILE, data)

def get_tag_map():
    return _load(TAG_FILE)

def save_tag_map(data):
    _save(TAG_FILE, data)