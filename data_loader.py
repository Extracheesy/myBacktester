import asyncio
import platform
from utilities.data_manager import ExchangeDataManager
import os
from vectorbtpro import *
import numpy as np
import pandas as pd

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


class DataLoaderVBT:
    def __init__(self, start_date, end_date, path):
        self.start_date = start_date
        self.end_date = end_date
        self.path = path

    # === Data Fetching and Storage ===
    def fetch_data(self, symbols, tf):
        # Convert the list of symbols into a string separated by '-'
        symbols_str = '-'.join(symbols)
        timeframe_str = '-'.join(tf)

        # Remove any unwanted characters from start_date and end_date
        start_date_str = self.start_date.replace('-', '')
        end_date_str = self.end_date.replace('-', '')

        # Ensure the directory exists
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        # Generate the filename
        filename = os.path.join(self.path, f"{symbols_str}_{timeframe_str}_{start_date_str}_{end_date_str}.h5")

        if os.path.exists(filename):
            # data = vbt.HDFData.pull(filename)
            data = vbt.BinanceData.from_hdf(filename)
        else:
            data = vbt.BinanceData.pull(
                symbols,
                start=self.start_date,
                end=self.end_date,
                timeframe=tf
            )

            if not os.path.exists('data_pro'):
                os.makedirs('data_pro')

            data.to_hdf(filename)

        return data