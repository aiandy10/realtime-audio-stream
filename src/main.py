import asyncio

from src.audio_capture import AudioCapture
from src.chunker import AudioChunker
from src.vad import VADProcessor
from src.websocket_client import WebSocketClient


class App:
    def __init__(self):
        self.audio = AudioCapture()
        self.chunker = AudioChunker()
        self.vad = VADProcessor(aggressiveness=3)
        self.ws = WebSocketClient()

        self.running = True

    async def receive_loop(self):
        while True:
            msg = await self.ws.receive()
            if msg:
                print("📝 Transcript:", msg)

    async def run(self):
        try:
            await self.ws.connect()
            ws_connected = True
        except Exception as e:
            print(f"[WebSocket] Not connected: {e}")
            ws_connected = False

        # Start listening for transcripts
        if ws_connected:
            asyncio.create_task(self.receive_loop())

        self.audio.start()
        q = self.audio.get_audio_queue()

        print("[System] Running... Press Ctrl+C to stop")

        try:
            while self.running:
                data = q.get()

                self.chunker.add_audio(data)
                chunk = self.chunker.get_chunk()

                if chunk is None:
                    continue

                if not self.vad.is_speech(chunk):
                    print("⚫ Skipping silence")
                    continue

                print("🚀 Sending chunk:", chunk.shape)

                if ws_connected:
                    await self.ws.send_audio(chunk)
                else:
                    print("📡 No backend connected")

        except KeyboardInterrupt:
            print("\n[System] Shutting down...")

        finally:
            self.audio.stop()
            if ws_connected:
                await self.ws.close()


def main():
    app = App()
    asyncio.run(app.run())


if __name__ == "__main__":
    main()