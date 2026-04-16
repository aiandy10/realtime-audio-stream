import numpy as np
from collections import deque
from config.settings import settings


class AudioChunker:
    def __init__(self):
        self.sample_rate = settings.SAMPLE_RATE

        self.window_size = settings.WINDOW_SIZE
        self.stride_size = settings.STRIDE_SIZE

        self.buffer = deque()
        self.current_size = 0

    def add_audio(self, audio_chunk: np.ndarray):
        """
        Add incoming audio chunk to buffer
        """
        if audio_chunk is None or len(audio_chunk) == 0:
            return

        # 🔥 ensure float32 consistency
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32)

        self.buffer.append(audio_chunk)
        self.current_size += len(audio_chunk)

    def get_chunk(self):
        """
        Returns a chunk if enough data is available
        """
        if self.current_size < self.window_size:
            return None

        if not self.buffer:
            return None

        # 🔥 Efficient concat
        full_audio = np.concatenate(self.buffer, axis=0)

        if len(full_audio) < self.window_size:
            return None

        # 🔥 Extract window
        chunk = full_audio[:self.window_size]

        # 🔥 Slide window (stride)
        remaining_audio = full_audio[self.stride_size:]

        # 🔥 Reset buffer cleanly
        self.buffer.clear()
        if len(remaining_audio) > 0:
            self.buffer.append(remaining_audio)

        self.current_size = len(remaining_audio)

        return chunk