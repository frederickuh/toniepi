import pygame
import time
import os
from config import AUDIO_FOLDER, DEFAULT_VOLUME
from storage import save_position, get_position

pygame.mixer.init()
pygame.mixer.music.set_volume(DEFAULT_VOLUME)

current_uid = None
start_time = 0

def play(uid, filename):
    global current_uid, start_time

    filepath = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.exists(filepath):
        print("Audio file missing:", filepath)
        return

    current_uid = uid
    pygame.mixer.music.load(filepath)
    pygame.mixer.music.play(start=get_position(uid))
    start_time = time.time()

def stop():
    global current_uid
    if current_uid:
        elapsed = time.time() - start_time
        save_position(current_uid, elapsed)
    pygame.mixer.music.stop()