import asyncio
import websockets


async def chat_client():
    async with websockets.connect("ws://localhost:8765") as websocket:
        while True:
            message = input("Enter a message: ")
            await websocket.send(message)
            response = await websocket.recv()
            print(response)


async def main():
    await chat_client()

if __name__ == "__main__":
    asyncio.run(main())
