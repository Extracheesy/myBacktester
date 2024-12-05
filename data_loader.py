import asyncio
import platform
from utilities.data_manager import ExchangeDataManager

class DataLoader:
    def __init__(self, exchange_name, path_download):
        self.exchange_name = exchange_name
        self.path_download = path_download
        self.exchange = ExchangeDataManager(exchange_name=self.exchange_name, path_download=self.path_download)

        # Set the correct event loop policy for Windows
        if platform.system() == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def download_data(self, coins, intervals):
        """Download historical data for specified coins and intervals."""
        await self.exchange.download_data(coins=coins, intervals=intervals)

    def load_data(self, coin, interval):
        """Load historical data from the database."""
        return self.exchange.load_data(coin=coin, interval=interval)

    def explore_data(self):
        """Explore data using the ExchangeDataManager's method."""
        self.exchange.explore_data()
