import aiohttp
import asyncio
import argparse
import datetime
import json

API_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="


async def get_exchange_rates(days):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(days):
            task = asyncio.ensure_future(get_exchange_rate(session, i))
            tasks.append(task)
        return await asyncio.gather(*tasks)


async def get_exchange_rate(session, days_ago):
    date = (datetime.date.today() -
            datetime.timedelta(days=days_ago)).strftime("%d.%m.%Y")
    async with session.get(f"{API_URL}{date}") as response:
        if response.status == 200:
            data = await response.json()
            exchange_rates = {}
            for rate in data['exchangeRate']:
                if rate['currency'] == 'EUR' or rate['currency'] == 'USD':
                    exchange_rates[rate['currency']] = {
                        'sale': rate['saleRate'],
                        'purchase': rate['purchaseRate']
                    }
            return {date: exchange_rates}
        else:
            return {date: "Error: Unable to fetch data."}


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "days", type=int, help="Number of days to retrieve exchange rates")
    return parser.parse_args()


def main():
    args = parse_arguments()
    days = min(args.days, 10)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(get_exchange_rates(days))

    # Записуємо результат у файл у форматі JSON
    with open("exchange_rates.json", "w") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    print("Результат програми:")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
