# import asyncio
# import websockets
# import struct
# import numpy as np
# from typing import AsyncGenerator


# class AudioReceiver:
#     def __init__(self, url: str):
#         self.url = url
#         self.connection = None

#     async def connect(self):
#         while True:
#             try:
#                 self.connection = await websockets.connect(
#                     self.url,
#                     max_size=None,
#                     ping_interval=20,
#                     ping_timeout=20,
#                 )
#                 print(f"[Receiver] Connected to {self.url}")
#                 return
#             except Exception as e:
#                 print(f"[Receiver] Connection failed: {e}")
#                 await asyncio.sleep(2)

#     async def receive_loop(self) -> AsyncGenerator[np.ndarray, None]:
#         """
#         Yields decoded audio chunks as float32 numpy arrays
#         """
#         if self.connection is None:
#             await self.connect()

#         while True:
#             try:
#                 data = await self.connection.recv()

#                 if not isinstance(data, (bytes, bytearray)):
#                     continue  # ignore non-binary frames

#                 # ---- Decode header ----
#                 if len(data) < 4:
#                     print("[Receiver] Invalid packet (too small)")
#                     continue

#                 sample_rate = struct.unpack("I", data[:4])[0]

#                 # ---- Decode audio ----
#                 audio_int16 = np.frombuffer(data[4:], dtype=np.int16)

#                 # Convert to float32 [-1, 1]
#                 audio_float32 = audio_int16.astype(np.float32) / 32768.0

#                 yield audio_float32, sample_rate

#             except websockets.exceptions.ConnectionClosed:
#                 print("[Receiver] Connection lost. Reconnecting...")
#                 self.connection = None
#                 await self.connect()
            

#             except Exception as e:
#                 print(f"[Receiver] Error: {e}")
#                 await asyncio.sleep(0.1)

import asyncio
import websockets


class TranscriptReceiver:
    def __init__(self, url: str):
        self.url = url
        self.connection = None

        #  Maintain single evolving transcript
        self.current_text = ""

    async def connect(self):
        while True:
            try:
                self.connection = await websockets.connect(
                    self.url,
                    max_size=None,
                    ping_interval=20,
                    ping_timeout=20,
                )
                print(f"[Receiver] Connected to {self.url}")
                return
            except Exception as e:
                print(f"[Receiver] Connection failed: {e}")
                await asyncio.sleep(2)

    # -------------------------
    # MERGE LOGIC
    # -------------------------

    def merge_text(self, prev, new):
        """
        Simple overlap-based merge
        """
        if not prev:
            return new

        max_overlap = min(len(prev), len(new))

        for i in range(max_overlap, 0, -1):
            if prev.endswith(new[:i]):
                return prev + new[i:]

        return prev + " " + new

    # -------------------------
    # MAIN LOOP
    # -------------------------

    async def receive_loop(self):
        if self.connection is None:
            await self.connect()

        while True:
            try:
                data = await self.connection.recv()

                #  Expect TEXT now (not bytes)
                if not isinstance(data, str):
                    continue

                new_text = data

                #  Merge into single paragraph
                self.current_text = self.merge_text(self.current_text, new_text)

                #  Replace output (not append)
                print("\r" + self.current_text, end="", flush=True)

            except websockets.exceptions.ConnectionClosed:
                print("\n[Receiver] Connection lost. Reconnecting...")
                self.connection = None
                await self.connect()

            except Exception as e:
                print(f"\n[Receiver] Error: {e}")
                await asyncio.sleep(0.1)


# -------------------------
# RUN
# -------------------------

async def main():
    receiver = TranscriptReceiver("ws://localhost:8765")
    await receiver.receive_loop()


if __name__ == "__main__":
    asyncio.run(main())

                