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
        self.buffer.append(audio_chunk)
        self.current_size += len(audio_chunk)

    def get_chunk(self):
        """
        Returns a chunk if enough data is available
        """
        if self.current_size < self.window_size:
            return None

        # Combine buffer into single array
        full_audio = np.concatenate(list(self.buffer), axis=0)

        # Take window
        chunk = full_audio[:self.window_size]

        # Remove stride amount from buffer
        remaining_audio = full_audio[self.stride_size:]

        # Reset buffer with remaining audio
        self.buffer = deque([remaining_audio])
        self.current_size = len(remaining_audio)

        return chunk