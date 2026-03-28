import sounddevice as sd
import numpy as np
import queue
from config.settings import settings


class AudioCapture:
    def __init__(self):
        self.sample_rate = settings.SAMPLE_RATE
        self.channels = settings.CHANNELS
        self.dtype = settings.DTYPE

        self.audio_queue = queue.Queue()
        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"[Audio Error]: {status}")

        # VERY IMPORTANT: do NOT process here
        # just push to queue
        self.audio_queue.put(indata.copy())

    def start(self):
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._callback
        )
        self.stream.start()
        print("[AudioCapture] Started microphone stream")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("[AudioCapture] Stopped microphone stream")

    def get_audio_queue(self):
        return self.audio_queue