import asyncio
import websockets
import uuid
import struct
import numpy as np

HOST = "0.0.0.0"
PORT = 8765

# 🔹 Active connections
connections = {}

# 🔹 Processing queue
audio_queue = asyncio.Queue(maxsize=1000)


# -------------------------
# CONNECTION MANAGEMENT
# -------------------------

async def register(websocket):
    session_id = str(uuid.uuid4())
    connections[session_id] = websocket
    print(f"🟢 Connected: {session_id} | Total: {len(connections)}")
    return session_id


async def unregister(session_id):
    if session_id in connections:
        del connections[session_id]
        print(f"🔴 Disconnected: {session_id} | Total: {len(connections)}")


# -------------------------
# AUDIO DECODER
# -------------------------

def decode_audio(payload: bytes):
    if len(payload) < 4:
        return None, None

    sample_rate = struct.unpack("I", payload[:4])[0]
    audio = np.frombuffer(payload[4:], dtype=np.float32)

    return audio, sample_rate


# -------------------------
# CONNECTION HANDLER
# -------------------------

async def handle_connection(websocket):
    session_id = await register(websocket)

    try:
        async for message in websocket:

            if not isinstance(message, (bytes, bytearray)):
                continue

            #  push to queue (DO NOT PROCESS HERE)
            try:
                await audio_queue.put({
                    "session_id": session_id,
                    "payload": message
                })
            except asyncio.QueueFull:
                print(" Queue full — dropping chunk")

    except websockets.exceptions.ConnectionClosed:
        pass

    finally:
        await unregister(session_id)


# -------------------------
# WORKER (REAL, CLEAN)
# -------------------------

async def worker():
    while True:
        task = await audio_queue.get()

        session_id = task["session_id"]
        payload = task["payload"]

        #  Decode once here
        audio, sample_rate = decode_audio(payload)

        if audio is None:
            audio_queue.task_done()
            continue

        # -------------------------
        #  FUTURE: MODEL CALL HERE
        # -------------------------
        # text = await whisper(audio)

        # -------------------------
        #  TEMP: minimal ACK (no mock logic)
        # -------------------------
        if session_id in connections:
            try:
                await connections[session_id].send("...")  # placeholder
            except:
                pass

        audio_queue.task_done()


# -------------------------
# MAIN
# -------------------------

async def main():
    print(f" Server running on ws://{HOST}:{PORT}")

    #  Start workers
    for _ in range(4):
        asyncio.create_task(worker())

    async with websockets.serve(
        handle_connection,
        HOST,
        PORT,
        max_size=None,
        ping_interval=20,
        ping_timeout=20
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())