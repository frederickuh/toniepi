import os
import pygame
import numpy as np
import time

class AudioPlayer:
    SUPPORTED_FORMATS = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Set volume to initial value
        self.set_volume(.01)

        self.playlist = []
        self.current_index = -1
        self.is_paused = False

        # Create custom event for track ending
        self.TRACK_END_EVENT = pygame.USEREVENT + 1
        pygame.mixer.music.set_endevent(self.TRACK_END_EVENT)

    def get_volume(self):
        volume = pygame.mixer.music.get_volume()

        return 20*np.log10( volume )
    
    
    def set_volume(self,volume):
        volume = min(volume,.05)

        pygame.mixer.music.set_volume(volume)

    def volume_up(self):
        newVolume = self.get_volume() + 3

        self.set_volume( np.power(10,(newVolume/20)) )

        return self.get_volume()

    def volume_down(self):
        newVolume = self.get_volume() - 3

        self.set_volume( np.power(10,(newVolume/20)) )

        return self.get_volume()


    # ----------------------------
    # Playlist Loading
    # ----------------------------

    def load_folder(self, folder_path, recursive=False):
        self.playlist.clear()
        self.current_index = -1

        if recursive:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if self._is_audio(file):
                        self.playlist.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                full_path = os.path.join(folder_path, file)
                if os.path.isfile(full_path) and self._is_audio(file):
                    self.playlist.append(full_path)

        self.playlist.sort()

    def _is_audio(self, filename):
        return os.path.splitext(filename)[1].lower() in self.SUPPORTED_FORMATS

    # ----------------------------
    # Playback Controls
    # ----------------------------

    def play(self, index=None):
        if not self.playlist:
            print("Playlist is empty.")
            return

        if index is not None:
            if 0 <= index < len(self.playlist):
                self.current_index = index
            else:
                print("Invalid index.")
                return

        if self.current_index == -1:
            self.current_index = 0

        track = self.playlist[self.current_index]
        pygame.mixer.music.load(track)
        pygame.mixer.music.play()
        self.is_paused = False

        print(f"Now playing: {os.path.basename(track)}")

    def pause(self):
        if self.is_paused == False:
            pygame.mixer.music.pause()
            self.is_paused = True
        else:
            pygame.mixer.music.unpause()
            self.is_paused = False
            

    def stop(self):
        pygame.mixer.music.stop()
        self.is_paused = False

    def next_track(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self.play()

    def previous_track(self):
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self.play()

    # ----------------------------
    # End Event Handling
    # ----------------------------

    def handle_event(self, event):
        """Call this from your main pygame loop."""
        if event.type == self.TRACK_END_EVENT:
            self._on_track_end()

    def _on_track_end(self):
        """Internal 'callback' for when a track finishes."""
        print("Track finished.")
        self.next_track()

    # ----------------------------
    # Cleanup
    # ----------------------------

    def quit(self):
        pygame.mixer.quit()
        pygame.quit()