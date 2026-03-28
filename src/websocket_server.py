import asyncio
import websockets
import numpy as np
import struct

HOST = "0.0.0.0"
PORT = 8765

# 🔥 CONFIG (tune later)
SAMPLE_RATE = 16000
WINDOW_SECONDS = 8      # how much audio Whisper sees
STRIDE_SECONDS = 3      # how often we run inference

WINDOW_SIZE = SAMPLE_RATE * WINDOW_SECONDS
STRIDE_SIZE = SAMPLE_RATE * STRIDE_SECONDS


class AudioSession:
    def __init__(self):
        self.buffer = np.array([], dtype=np.float32)
        self.last_processed_index = 0

    def add_chunk(self, audio):
        self.buffer = np.concatenate([self.buffer, audio])

    def get_buffer_duration(self):
        return len(self.buffer) / SAMPLE_RATE

    def get_next_window(self):
        """
        Returns next sliding window if enough new data exists
        """
        if len(self.buffer) < WINDOW_SIZE:
            return None

        if self.last_processed_index + WINDOW_SIZE > len(self.buffer):
            return None

        start = self.last_processed_index
        end = start + WINDOW_SIZE

        window = self.buffer[start:end]

        # Move forward by stride (NOT full window → overlap)
        self.last_processed_index += STRIDE_SIZE

        return window


async def fake_whisper_inference(audio_window):
    """
    🔥 Replace this later with real Whisper
    """
    duration = len(audio_window) / SAMPLE_RATE
    print(f"🧠 [Whisper] Processing {duration:.2f}s audio...")
    
    # Simulated result
    return "transcribed text..."


async def handle_connection(websocket):
    print("🟢 Client connected")

    session = AudioSession()

    try:
        async for message in websocket:

            # -------------------------------
            # Decode message (header + audio)
            # -------------------------------
            sample_rate = struct.unpack("I", message[:4])[0]
            audio_bytes = message[4:]

            audio = np.frombuffer(audio_bytes, dtype=np.int16)
            audio = audio.astype("float32") / 32768.0

            # -------------------------------

            session.add_chunk(audio)

            print(
                f"📥 Chunk | SR: {sample_rate} | Samples: {len(audio)} | Buffer: {session.get_buffer_duration():.2f}s"
            )

            # -------------------------------
            # 🔥 SLIDING WINDOW TRIGGER
            # -------------------------------
            while True:
                window = session.get_next_window()

                if window is None:
                    break

                # 🔥 Whisper call
                text = await fake_whisper_inference(window)

                # Send result back
                await websocket.send(text)

    except websockets.exceptions.ConnectionClosed:
        print("🔴 Client disconnected")


async def main():
    print(f"🚀 WebSocket Server running on ws://{HOST}:{PORT}")
    async with websockets.serve(handle_connection, HOST, PORT, max_size=None):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())