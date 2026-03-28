import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()


class Settings:
    # =========================
    # WebSocket Configuration
    # =========================
    WS_URL: str = os.getenv("WS_URL", "ws://localhost:8765")

    # =========================
    # Audio Configuration
    # =========================
    SAMPLE_RATE: int = int(os.getenv("SAMPLE_RATE", 16000))
    CHANNELS: int = int(os.getenv("CHANNELS", 1))
    DTYPE: str = "int16"  # fixed for Whisper compatibility

    # =========================
    # Chunking Configuration
    # =========================
    WINDOW_DURATION: int = int(os.getenv("WINDOW_DURATION", 3))  # seconds
    STRIDE_DURATION: int = int(os.getenv("STRIDE_DURATION", 1))  # seconds

    @property
    def WINDOW_SIZE(self) -> int:
        return self.SAMPLE_RATE * self.WINDOW_DURATION

    @property
    def STRIDE_SIZE(self) -> int:
        return self.SAMPLE_RATE * self.STRIDE_DURATION


# Singleton instance (use everywhere)
settings = Settings()