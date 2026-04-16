import sounddevice as sd
import numpy as np
import queue
from config.settings import settings


class AudioCapture:
    def __init__(self):
        self.sample_rate = settings.SAMPLE_RATE
        self.channels = settings.CHANNELS

        # 🔥 force float32 internally (important)
        self.dtype = "float32"

        # 🔥 prevent memory explosion
        self.audio_queue = queue.Queue(maxsize=100)

        self.stream = None

    def _callback(self, indata, frames, time, status):
        if status:
            print(f"[Audio Error]: {status}")

        try:
            # 🔥 handle mono / stereo safely
            if indata.ndim == 2:
                mono_audio = indata[:, 0]
            else:
                mono_audio = indata

            # 🔥 ensure float32
            mono_audio = mono_audio.astype(np.float32)

            # 🔥 non-blocking put (important)
            try:
                self.audio_queue.put_nowait(mono_audio.copy())
            except queue.Full:
                # drop frame instead of blocking
                pass

        except Exception as e:
            print(f"[AudioCapture] Callback error: {e}")

    def start(self):
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=self.dtype,
                callback=self._callback
            )
            self.stream.start()
            print("[AudioCapture] Started microphone stream")

        except Exception as e:
            print(f"[AudioCapture] Failed to start: {e}")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            print("[AudioCapture] Stopped microphone stream")

    def get_audio_queue(self):
        return self.audio_queue