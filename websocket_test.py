import websockets
import asyncio

async def listen():
    async with websockets.connect("wss://awbw.amarriner.com/node/game/802669", extra_headers={"Cookie": "PHPSESSID=fbfff137fde4c7cec675a213280f3c19; awbw_username=boundtotheearth2; awbw_password=%2A5B808C1E2B0629D8DF35430B8BEC89FBEFE33EC0"}) as websocket:
        message = input("Send:")
        await websocket.send(message)
        while True:
            pass
        # while True:
        #     message = await websocket.recv()
        #     print(message)

asyncio.run(listen())