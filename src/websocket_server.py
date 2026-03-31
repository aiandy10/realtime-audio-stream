import asyncio
import websockets

HOST = "0.0.0.0"
PORT = 8765

# Store all connected clients
connected_clients = set()


async def register(websocket):
    connected_clients.add(websocket)
    print(f"🟢 Client connected | Total: {len(connected_clients)}")


async def unregister(websocket):
    connected_clients.remove(websocket)
    print(f"🔴 Client disconnected | Total: {len(connected_clients)}")


async def broadcast(sender, message):
    """
    Send incoming audio to all OTHER clients
    """
    dead_clients = []

    for client in connected_clients:
        if client != sender:
            try:
                await client.send(message)
            except:
                dead_clients.append(client)

    # Remove broken connections
    for dc in dead_clients:
        connected_clients.remove(dc)


async def handle_connection(websocket):
    await register(websocket)

    try:
        async for message in websocket:
            print(f"📥 Received {len(message)} bytes")

            # 🔥 Just forward — no processing
            await broadcast(websocket, message)

    except websockets.exceptions.ConnectionClosed:
        pass

    finally:
        await unregister(websocket)


async def main():
    print(f"🚀 Broadcast Server running on ws://{HOST}:{PORT}")

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