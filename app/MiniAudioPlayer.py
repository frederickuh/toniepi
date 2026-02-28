import miniaudio
import threading
import time
from typing import List, Callable, Optional
import math
import os


class MiniAudioPlayer:
    def __init__(
        self,
        on_track_end: Optional[Callable[[str], None]] = None,
        fade_in_duration: float = 1.0,
        fade_out_duration: float = 1.0,
        crossfade_duration: float = 3.0,
    ):
        self.playlist: List[str] = []
        self.current_index: int = -1

        self._device: Optional[miniaudio.PlaybackDevice] = None
        self._decoder: Optional[miniaudio.Decoder] = None
        self._next_decoder: Optional[miniaudio.Decoder] = None

        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        self._playing = False
        self._paused = False
        self._stop_flag = False
        self._manual_stop = False

        self._volume = 1.0  # 0.0 – 1.0

        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration
        self.crossfade_duration = crossfade_duration

        self._on_track_end = on_track_end

    # -------------------------
    # Playlist
    # -------------------------

    def load(self, files: List[str]):
        with self._lock:
            self.stop()
            self.playlist = files
            self.current_index = 0 if files else -1

    def next(self):
        with self._lock:
            if not self.playlist:
                return
            self.stop()
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play()

    def previous(self):
        with self._lock:
            if not self.playlist:
                return
            self.stop()
            self.current_index = (self.current_index - 1) % len(self.playlist)
            self.play()

    # -------------------------
    # Volume Control
    # -------------------------

    def set_volume(self, volume: float):
        """Set volume (0.0 – 1.0)"""
        with self._lock:
            self._volume = max(0.0, min(1.0, volume))

    def get_volume(self) -> float:
        return self._volume

    # -------------------------
    # Playback Controls
    # -------------------------

    def play(self):
        with self._lock:
            if not self.playlist or self.current_index < 0:
                return

            if self._playing and self._paused:
                self._paused = False
                return

            if self._playing:
                return

            self._stop_flag = False
            self._manual_stop = False
            self._paused = False

            self._thread = threading.Thread(
                target=self._play_current,
                daemon=True,
            )
            self._thread.start()

    def pause(self):
        self._paused = True

    def stop(self):
        self._manual_stop = True
        self._fade_out_and_stop()

    # -------------------------
    # Fading
    # -------------------------

    def _fade_out_and_stop(self):
        if not self._decoder:
            return

        fade_frames = int(self.fade_out_duration * self._decoder.sample_rate)
        self._apply_fade_out = fade_frames
        self._stop_flag = True

        if self._thread and self._thread.is_alive():
            self._thread.join()

    # -------------------------
    # Seek
    # -------------------------

    def seek(self, seconds: float):
        if self._decoder:
            frame = int(seconds * self._decoder.sample_rate)
            self._decoder.seek(frame)

    # -------------------------
    # Internal Playback
    # -------------------------

    def _play_current(self):
        filename = self.playlist[self.current_index]

        try:
            self._decoder = miniaudio.decode_file(filename)
            self._device = miniaudio.PlaybackDevice()
            self._playing = True

            sample_rate = self._decoder.sample_rate
            fade_in_frames = int(self.fade_in_duration * sample_rate)
            crossfade_frames = int(self.crossfade_duration * sample_rate)

            frames_played = 0

            def generator():
                nonlocal frames_played

                while not self._stop_flag:

                    if self._paused:
                        time.sleep(0.05)
                        continue

                    data = self._decoder.read_frames(1024)
                    if not data:
                        break

                    data = bytearray(data)
                    frame_count = len(data) // 2  # assuming 16-bit

                    # Apply fade-in
                    if frames_played < fade_in_frames:
                        for i in range(frame_count):
                            fade_ratio = frames_played / max(1, fade_in_frames)
                            self._scale_sample(data, i, fade_ratio * self._volume)
                            frames_played += 1
                    else:
                        for i in range(frame_count):
                            self._scale_sample(data, i, self._volume)

                    yield bytes(data)

                self._playing = False

            self._device.start(generator())

            while self._device.is_started() and not self._stop_flag:
                time.sleep(0.1)

        finally:
            self._cleanup_after_track(filename)

    # -------------------------
    # Sample Scaling
    # -------------------------

    def _scale_sample(self, buffer: bytearray, index: int, volume: float):
        """Scale 16-bit signed sample"""
        i = index * 2
        sample = int.from_bytes(buffer[i:i+2], "little", signed=True)
        sample = int(sample * volume)
        buffer[i:i+2] = int(sample).to_bytes(2, "little", signed=True)

    # -------------------------
    # Track Cleanup + Auto Next
    # -------------------------

    def _cleanup_after_track(self, filename: str):
        if self._device:
            self._device.close()
            self._device = None

        self._playing = False

        if not self._manual_stop and self.playlist:
            if self._on_track_end:
                self._on_track_end(filename)

            # advance
            self.current_index = (self.current_index + 1) % len(self.playlist)
            self.play()

    # -------------------------
    # Info
    # -------------------------

    def is_playing(self):
        return self._playing and not self._paused

    def is_paused(self):
        return self._paused

    def current_track(self):
        if 0 <= self.current_index < len(self.playlist):
            return self.playlist[self.current_index]
        return None
    
    def load_from_folder(self, folder_path: str, recursive: bool = False):
        """
        Load all supported audio files from a folder into the playlist.
        If recursive=True, subfolders are included.
        """

        if not os.path.isdir(folder_path):
            raise ValueError(f"Not a valid directory: {folder_path}")

        supported_extensions = {
            ".mp3", ".wav", ".flac", ".ogg",
            ".m4a", ".aac"
        }

        audio_files = []

        if recursive:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_extensions:
                        audio_files.append(os.path.join(root, file))
        else:
            for file in os.listdir(folder_path):
                full_path = os.path.join(folder_path, file)
                if os.path.isfile(full_path):
                    ext = os.path.splitext(file)[1].lower()
                    if ext in supported_extensions:
                        audio_files.append(full_path)

        audio_files.sort()

        if not audio_files:
            raise ValueError("No supported audio files found in folder.")

        self.load(audio_files)