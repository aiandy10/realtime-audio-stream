import websockets
import numpy as np
import struct
import asyncio
from config.settings import settings


class WebSocketClient:
    def __init__(self):
        self.url = settings.WS_URL
        self.connection = None

    async def connect(self):
        try:
            self.connection = await websockets.connect(
                self.url,
                max_size=None,  # important for audio streaming
                ping_interval=20,
                ping_timeout=20,
            )
            print(f"[WebSocket] Connected to {self.url}")
        except Exception as e:
            print(f"[WebSocket] Connection failed: {e}")
            self.connection = None

    async def send_audio(self, audio_chunk: np.ndarray):
        """
        Send audio as:
        [4 bytes sample_rate][raw int16 audio bytes]
        """
        if self.connection is None:
            print("[WebSocket] Not connected. Attempting reconnect...")
            await self.connect()
            if self.connection is None:
                return

        try:
            sample_rate = settings.SAMPLE_RATE

            # Ensure correct dtype
            if audio_chunk.dtype != np.int16:
                audio_chunk = (audio_chunk * 32768.0).astype(np.int16)

            # Header (4 bytes unsigned int)
            header = struct.pack("I", sample_rate)

            # Audio bytes
            audio_bytes = audio_chunk.tobytes()

            payload = header + audio_bytes

            await self.connection.send(payload)

        except Exception as e:
            print(f"[WebSocket] Send failed: {e}")
            await self.close()

    async def receive(self):
        if self.connection is None:
            return None

        try:
            msg = await self.connection.recv()
            return msg
        except Exception as e:
            print(f"[WebSocket] Receive failed: {e}")
            return None

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            print("[WebSocket] Connection closed")