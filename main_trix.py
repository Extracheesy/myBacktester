import asyncio
from data_loader import DataLoader
from multi_param_strategy import DataLoader, MultiParamStrategy
import itertools

def main():
    # Initialize DataLoader
    exchange_name = "binance"
    path_download = "./database/exchanges"
    data_loader = DataLoader(exchange_name=exchange_name, path_download=path_download)

    # Define coins and intervals
    coins_to_download = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    intervals = ["1h", "2h", "4h"]

    # Download data
    async def download():
        await data_loader.download_data(coins=coins_to_download, intervals=intervals)

    asyncio.run(download())

    # Explore data
    data_loader.explore_data()

    exchange_name = "binance"
    path_download = "./database/exchanges"

    data_loader = DataLoader(exchange_name, path_download)

    trading_pairs = coins_to_download
    timeframes = intervals
    trix_lengths = [7, 11, 15, 20]
    trix_signal_lengths = [7, 11, 15, 20]
    trix_signal_types = ["sma", "ema"]
    long_ma_lengths = [200, 300, 500]

    combinations = list(itertools.product(
        timeframes, trading_pairs,
        itertools.product(trix_lengths, trix_signal_lengths, trix_signal_types, long_ma_lengths)
    ))

    params_combinations = [
        (tf, pair, {"trix_length": trix[0], "trix_signal_length": trix[1],
                    "trix_signal_type": trix[2], "long_ma_length": trix[3]})
        for tf, pair, trix in combinations
    ]

    strategy_runner = MultiParamStrategy(data_loader, trading_pairs, timeframes, params_combinations)

    results = strategy_runner.run(
        initial_wallet=1000, leverage=1, start_date="2020-01-01", end_date=None
    )

    print(results)

if __name__ == "__main__":
    main()
