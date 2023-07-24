import asyncio
import websockets
import names
import json
import aiofile
import aiopath
from datetime import datetime, timedelta
import aiohttp
import logging

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date={}"
LOG_FILE_PATH = "exchange_log.txt"

logging.basicConfig(level=logging.INFO)


class ExchangeRates:
    async def fetch_exchange_rates(self, session, date):
        url = API_URL.format(date.strftime("%d.%m.%Y"))
        async with session.get(url) as response:
            data = await response.json()
            rates = {}
            for rate in data['exchangeRate']:
                if rate['currency'] in ['EUR', 'USD']:
                    rates[rate['currency']] = {
                        'sale': round(float(rate['saleRateNB']), 1),
                        'purchase': round(float(rate['purchaseRateNB']), 1)
                    }
            return {date.strftime("%d.%m.%Y"): rates}

    async def get_exchange_rates(self, days=2):
        async with aiohttp.ClientSession() as session:
            start_date = datetime.now()
            exchange_rates = []
            for i in range(days):
                date = start_date - timedelta(days=i)
                exchange_rate = await self.fetch_exchange_rates(session, date)
                exchange_rates.append(exchange_rate)
            return exchange_rates


class ChatServer:
    clients = set()

    async def register(self, ws: websockets.WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: websockets.WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: websockets.WebSocketServerProtocol, path):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: websockets.WebSocketServerProtocol):
        async for message in ws:
            if message.startswith("exchange"):
                await self.process_exchange_command(ws, message)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def process_exchange_command(self, ws: websockets.WebSocketServerProtocol, message):
        try:
            _, *args = message.split()
            days = 2
            if args and args[0].isdigit():
                days = min(int(args[0]), 10)

            exchange_rates = await ExchangeRates().get_exchange_rates(days)
            response = json.dumps(exchange_rates, indent=2)

            # Logging the command execution to a file
            async with aiofile.async_open(LOG_FILE_PATH, mode='a') as f:
                await f.write(f"{datetime.now().isoformat()}: {response}\n")

            await ws.send(response)

        except Exception as e:
            await ws.send(f"Error processing command: {e}")


async def main():
    server = ChatServer()
    start_server = websockets.serve(server.ws_handler, 'localhost', 8765)

    async with start_server:
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
