import webrtcvad
import numpy as np
from config.settings import settings


class VADProcessor:
    def __init__(self, aggressiveness=2):
        """
        aggressiveness: 0 (least aggressive) → 3 (most aggressive)
        """
        self.vad = webrtcvad.Vad(aggressiveness)
        self.sample_rate = settings.SAMPLE_RATE

        # 10ms frame size (required by webrtcvad)
        self.frame_duration_ms = 10
        self.frame_size = int(self.sample_rate * self.frame_duration_ms / 1000)

    def is_speech(self, audio_chunk: np.ndarray) -> bool:
        """
        Determines if given audio chunk contains speech
        """
        if audio_chunk is None or len(audio_chunk) < self.frame_size:
            return False

        #  Convert float32 → int16 (CRITICAL)
        if audio_chunk.dtype != np.int16:
            audio_chunk = np.clip(audio_chunk, -1.0, 1.0)
            audio_chunk = (audio_chunk * 32767).astype(np.int16)

        speech_frames = 0
        total_frames = 0

        for i in range(0, len(audio_chunk), self.frame_size):
            frame = audio_chunk[i:i + self.frame_size]

            if len(frame) < self.frame_size:
                continue

            total_frames += 1

            try:
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    speech_frames += 1
            except Exception:
                continue

        if total_frames == 0:
            return False

        # 🔥 Slightly stricter threshold (more stable)
        return (speech_frames / total_frames) > 0.3