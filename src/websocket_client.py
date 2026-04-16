# import websockets
# import numpy as np
# import struct
# import asyncio
# from config.settings import settings


# class WebSocketClient:
#     def __init__(self):
#         self.url = settings.WS_URL
#         self.connection = None

#     async def connect(self):
#         try:
#             self.connection = await websockets.connect(
#                 self.url,
#                 max_size=None,
#                 ping_interval=20,
#                 ping_timeout=20,
#             )
#             print(f"[WebSocket] Connected to {self.url}")
#         except Exception as e:
#             print(f"[WebSocket] Connection failed: {e}")
#             self.connection = None

#     async def send_audio(self, audio_chunk: np.ndarray):
#         """
#         Send audio as:
#         [4 bytes sample_rate][raw int16 audio bytes]
#         """
#         if self.connection is None:
#             print("[WebSocket] Reconnecting...")
#             await self.connect()
#             if self.connection is None:
#                 print("[WebSocket] Dropping audio chunk (no connection)")
#                 return

#         try:
#             sample_rate = settings.SAMPLE_RATE

#             # 🔥 Ensure proper format
#             if audio_chunk.dtype != np.int16:
#                 audio_chunk = np.clip(audio_chunk, -1.0, 1.0)
#                 audio_chunk = (audio_chunk * 32767).astype(np.int16)

#             header = struct.pack("I", sample_rate)
#             audio_bytes = audio_chunk.tobytes()

#             payload = header + audio_bytes

#             await self.connection.send(payload)

#             # 🔥 Yield control (important for async stability)
#             await asyncio.sleep(0)

#         except Exception as e:
#             print(f"[WebSocket] Send failed: {e}")
#             await self.close()

#     async def receive(self):
#         if self.connection is None:
#             return None

#         try:
#             msg = await self.connection.recv()
#             return msg
#         except Exception as e:
#             print(f"[WebSocket] Receive failed: {e}")
#             return None

#     async def close(self):
#         if self.connection:
#             await self.connection.close()
#             self.connection = None
#             print("[WebSocket] Connection closed")

import websockets
import numpy as np
import struct
import asyncio
from config.settings import settings


class WebSocketClient:
    def __init__(self):
        self.url = settings.WS_URL
        self.connection = None
        self.lock = asyncio.Lock()

    # -------------------------
    # CONNECT (RETRY LOOP)
    # -------------------------

    async def connect(self):
        while self.connection is None:
            try:
                self.connection = await websockets.connect(
                    self.url,
                    max_size=None,
                    ping_interval=20,
                    ping_timeout=20,
                )
                print(f"[WebSocket] Connected to {self.url}")
            except Exception as e:
                print(f"[WebSocket] Connection failed: {e}")
                await asyncio.sleep(2)

    # -------------------------
    # SEND AUDIO
    # -------------------------

    async def send_audio(self, audio_chunk: np.ndarray):
        """
        Send:
        [4 bytes sample_rate][float32 PCM]
        """
        async with self.lock:
            if self.connection is None:
                await self.connect()

            try:
                sample_rate = settings.SAMPLE_RATE

                #  ensure float32
                if audio_chunk.dtype != np.float32:
                    audio_chunk = audio_chunk.astype(np.float32)

                audio_chunk = np.clip(audio_chunk, -1.0, 1.0)

                header = struct.pack("I", sample_rate)
                payload = header + audio_chunk.tobytes()

                await self.connection.send(payload)

            except Exception as e:
                print(f"[WebSocket] Send failed: {e}")
                await self._reset_connection()

    # -------------------------
    # RECEIVE TEXT
    # -------------------------

    async def receive(self):
        while True:
            if self.connection is None:
                await self.connect()

            try:
                msg = await self.connection.recv()

                if isinstance(msg, bytes):
                    continue  # ignore binary

                return msg

            except Exception as e:
                print(f"[WebSocket] Receive failed: {e}")
                await self._reset_connection()

    # -------------------------
    # RESET CONNECTION
    # -------------------------

    async def _reset_connection(self):
        try:
            if self.connection:
                await self.connection.close()
        except:
            pass

        self.connection = None
        await asyncio.sleep(1)

    # -------------------------
    # CLOSE
    # -------------------------

    async def close(self):
        if self.connection:
            await self.connection.close()
            self.connection = None
            print("[WebSocket] Connection closed")