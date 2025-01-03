import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from utilities.data_manager import ExchangeDataManager
from utilities.custom_indicators import Trix
from utilities.bt_analysis import get_metrics
from utilities.plot_analysis import plot_equity_vs_asset, plot_bar_by_month
import ta
import pandas as pd
import platform
from utilities.my_utils import save_dataframe_with_unique_filename, extract_symbols_from_files, remove_performed_symbols

from collections import defaultdict

import input_data

import time

# Set the correct event loop policy for Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class DataLoader:
    def __init__(self, exchange_name, path_download):
        self.exchange = ExchangeDataManager(exchange_name=exchange_name, path_download=path_download)

    async def download_data(self, coins, intervals):
        """Download historical data."""
        await self.exchange.download_data(coins=coins, intervals=intervals)

    def load_data(self, pair, timeframe):
        """Load historical data."""
        return self.exchange.load_data(pair, timeframe)


class Strategy:
    def __init__(self, df_list, oldest_pair, strategy_type, params):
        self.df_list = df_list
        self.oldest_pair = oldest_pair
        self.use_long = "long" in strategy_type
        self.use_short = "short" in strategy_type
        self.params = params

    def populate_indicators(self):
        for comb, df in self.df_list.items():
            params = self.params[comb]
            df.drop(columns=df.columns.difference(["open", "high", "low", "close", "volume"]), inplace=True)

            # Populate indicators
            trix_obj = Trix(
                close=df["close"],
                trix_length=params["trix_length"],
                trix_signal_length=params["trix_signal_length"],
                trix_signal_type=params["trix_signal_type"],
            )
            df["trix"] = trix_obj.get_trix_pct_line()
            df["trix_signal"] = trix_obj.get_trix_signal_line()
            df["trix_hist"] = df["trix"] - df["trix_signal"]
            df["long_ma"] = ta.trend.ema_indicator(df["close"], window=params["long_ma_length"])
            self.df_list[comb] = df

        return self.df_list[self.oldest_pair]

    def populate_buy_sell(self):
        full_list = []
        for comb, df in self.df_list.items():
            df["comb"] = comb
            full_list.append(df)

        df_full = pd.concat(full_list).sort_index()
        self.open_long_obj = (
            df_full[(df_full["trix_hist"] > 0) & (df_full["close"] > df_full["long_ma"])]
            .groupby("date")["comb"]
            .apply(list)
            .to_dict()
            if self.use_long
            else {}
        )
        self.close_long_obj = (
            df_full[(df_full["trix_hist"] < 0)]
            .groupby("date")["comb"]
            .apply(list)
            .to_dict()
            if self.use_long
            else {}
        )
        self.open_short_obj = (
            df_full[(df_full["trix_hist"] < 0) & (df_full["close"] < df_full["long_ma"])]
            .groupby("date")["comb"]
            .apply(list)
            .to_dict()
            if self.use_short
            else {}
        )
        self.close_short_obj = (
            df_full[(df_full["trix_hist"] > 0)]
            .groupby("date")["comb"]
            .apply(list)
            .to_dict()
            if self.use_short
            else {}
        )
        return self.df_list[self.oldest_pair]

    def run_backtest(self, initial_wallet=1000, leverage=1, start_date=None, end_date=None):
        # Filter the DataFrame based on the date range, handling None cases
        if start_date is not None:
            self.df_list = {
                k: v[v.index >= start_date] for k, v in self.df_list.items()
            }
        if end_date is not None:
            self.df_list = {
                k: v[v.index <= end_date] for k, v in self.df_list.items()
            }

        params = self.params
        df_ini = self.df_list[self.oldest_pair][:]
        wallet = initial_wallet
        long_exposition = 0
        short_exposition = 0
        maker_fee = 0.0002
        taker_fee = 0.0005
        trades = []
        days = []
        current_day = 0
        previous_day = 0
        current_positions = {}

        for index, ini_row in df_ini.iterrows():
            # -- Add daily report --
            current_day = index.day
            if previous_day != current_day:
                temp_wallet = wallet
                for comb in current_positions:
                    row = self.df_list[comb].loc[index]
                    position = current_positions[comb]
                    if position["side"] == "LONG":
                        close_price = row["open"]
                        trade_result = (close_price - position["price"]) / position[
                            "price"
                        ]
                        close_size = position["size"] + position["size"] * trade_result
                        fee = close_size * taker_fee
                        temp_wallet += close_size - position["size"] - fee
                    elif position["side"] == "SHORT":
                        close_price = row["open"]
                        trade_result = (position["price"] - close_price) / position[
                            "price"
                        ]
                        close_size = position["size"] + position["size"] * trade_result
                        fee = close_size * taker_fee
                        temp_wallet += close_size - position["size"] - fee

                days.append(
                    {
                        "day": str(index.year)
                               + "-"
                               + str(index.month)
                               + "-"
                               + str(index.day),
                        "wallet": temp_wallet,
                        "price": ini_row["open"],
                        "long_exposition": 0,
                        "short_exposition": 0,
                        "risk": 0,
                    }
                )
            previous_day = current_day

            close_long_row = (
                self.close_long_obj[index] if index in self.close_long_obj else []
            )
            close_short_row = (
                self.close_short_obj[index] if index in self.close_short_obj else []
            )
            if len(current_positions) > 0:
                # -- Close LONG --
                long_position_to_close = set(
                    {k: v for k, v in current_positions.items() if v["side"] == "LONG"}
                ).intersection(set(close_long_row))
                for comb in long_position_to_close:
                    row = self.df_list[comb].loc[index]
                    position = current_positions[comb]
                    close_price = row["close"]
                    trade_result = (close_price - position["price"]) / position["price"]
                    close_size = position["size"] + position["size"] * trade_result
                    fee = close_size * taker_fee
                    wallet += close_size - position["size"] - fee
                    trades.append(
                        {
                            "pair": comb,
                            "open_date": position["date"],
                            "close_date": index,
                            "position": position["side"],
                            "open_reason": position["reason"],
                            "close_reason": "Market",
                            "open_price": position["price"],
                            "close_price": close_price,
                            "open_fee": position["fee"],
                            "close_fee": fee,
                            "open_trade_size": position["size"],
                            "close_trade_size": close_size,
                            "wallet": wallet,
                        }
                    )
                    del current_positions[comb]

                # -- Close SHORT --
                short_position_to_close = set(
                    {k: v for k, v in current_positions.items() if v["side"] == "SHORT"}
                ).intersection(set(close_short_row))
                for comb in short_position_to_close:
                    row = self.df_list[comb].loc[index]
                    position = current_positions[comb]
                    close_price = row["close"]
                    trade_result = (position["price"] - close_price) / position["price"]
                    close_size = position["size"] + position["size"] * trade_result
                    fee = close_size * taker_fee
                    wallet += close_size - position["size"] - fee
                    trades.append(
                        {
                            "pair": comb,
                            "open_date": position["date"],
                            "close_date": index,
                            "position": position["side"],
                            "open_reason": position["reason"],
                            "close_reason": "Market",
                            "open_price": position["price"],
                            "close_price": close_price,
                            "open_fee": position["fee"],
                            "close_fee": fee,
                            "open_trade_size": position["size"],
                            "close_trade_size": close_size,
                            "wallet": wallet,
                        }
                    )
                    del current_positions[comb]

            # -- Check for opening position --
            # -- Open LONG --
            open_long_row = (
                self.open_long_obj[index] if index in self.open_long_obj else []
            )
            for comb in open_long_row:
                if comb not in current_positions:
                    row = self.df_list[comb].loc[index]
                    open_price = row["close"]
                    pos_size = params[comb]["size"] * wallet * leverage
                    fee = pos_size * taker_fee
                    pos_size -= fee
                    wallet -= fee
                    current_positions[comb] = {
                        "size": pos_size,
                        "date": index,
                        "price": open_price,
                        "fee": fee,
                        "reason": "Market",
                        "side": "LONG",
                    }
                    long_exposition += 0
            # -- Open SHORT --
            open_short_row = (
                self.open_short_obj[index] if index in self.open_short_obj else []
            )
            for comb in open_short_row:
                if comb not in current_positions:
                    row = self.df_list[comb].loc[index]
                    open_price = row["close"]
                    pos_size = params[comb]["size"] * wallet * leverage
                    fee = pos_size * taker_fee
                    pos_size -= fee
                    wallet -= fee
                    current_positions[comb] = {
                        "size": pos_size,
                        "date": index,
                        "price": open_price,
                        "fee": fee,
                        "reason": "Market",
                        "side": "SHORT",
                    }
                    short_exposition += 0

        if len(trades) == 0:
            # raise ValueError("No trades have been made")
            return {
                "sharpe_ratio": 0,
                'win_rate': 0,
                'avg_profit': 0,
                'total_trades': 0,
                'max_drawdown': 0,
                "wallet": 0,
                "trades": pd.DataFrame,
                "days": pd.DataFrame,
            }

        df_days = pd.DataFrame(days)
        df_days["day"] = pd.to_datetime(df_days["day"])
        df_days = df_days.set_index(df_days["day"])

        df_trades = pd.DataFrame(trades)
        df_trades["open_date"] = pd.to_datetime(df_trades["open_date"])
        df_trades = df_trades.set_index(df_trades["open_date"])

        return get_metrics(df_trades, df_days) | {
            "wallet": wallet,
            "trades": df_trades,
            "days": df_days,
        }


def process_combination(combo, data_loader, nb_comb, current_index):
    tf, pair, params = combo
    print(f"Processing combination {current_index}/{nb_comb}...")

    # Load data
    df = data_loader.load_data(pair, tf)
    df["pair"] = pair
    df["tf"] = tf
    df_list = {f"{tf}-{pair}": df}

    # Initialize strategy and run backtest
    strategy = Strategy(df_list, f"{tf}-{pair}", ["long"], {f"{tf}-{pair}": params})
    strategy.populate_indicators()
    strategy.populate_buy_sell()
    dct_result = strategy.run_backtest(initial_wallet=1000, leverage=1, start_date="2020-01-01", end_date=None)

    # Filter and return result
    exclude_fields = {'trades', 'days'}
    filtered_bt_result = {k: v for k, v in dct_result.items() if k not in exclude_fields}
    combined_data = {
        'timeframe': tf,
        'param_set': "p1",
        'pair': pair,
        **params,
        **filtered_bt_result
    }

    return pd.DataFrame([combined_data])


async def main():
    # Start the timer
    start_time = time.time()

    # Initialize DataLoader
    exchange_name = input_data.exchange_name
    if input_data.COLAB:
        dir_colab = '/content/drive/My Drive/Colab Notebooks/param_optimization/'
        path_download = dir_colab + "/database/exchanges"
    else:
        path_download = "./database/exchanges"
    data_loader = DataLoader(exchange_name=exchange_name, path_download=path_download)

    # Define parameters
    coins_to_download = input_data.lst_coin
    intervals = input_data.timeframes
    trix_lengths = input_data.trix_lengths
    trix_signal_lengths = input_data.trix_signal_lengths
    trix_signal_types = input_data.trix_signal_types
    long_ma_lengths = input_data.long_ma_lengths
    trix_size = input_data.size

    await data_loader.download_data(coins=coins_to_download, intervals=intervals)

    combinations = list(itertools.product(
        intervals, coins_to_download,
        itertools.product(trix_lengths, trix_signal_lengths, trix_signal_types, long_ma_lengths, trix_size)
    ))
    params_combinations = [
        (tf, pair, {"trix_length": trix[0], "trix_signal_length": trix[1],
                    "trix_signal_type": trix[2], "long_ma_length": trix[3], "size": trix[4]})
        for tf, pair, trix in combinations
    ]

    nb_comb = len(params_combinations)
    print(f"Total combinations: {nb_comb}")

    grouped_by_symbol = defaultdict(list)
    for item in params_combinations:
        _, symbol, params = item
        grouped_by_symbol[symbol].append(item)

    # Get a list of unique symbols
    symbols = list(grouped_by_symbol.keys())
    already_performed = extract_symbols_from_files("split_results")
    symbols = remove_performed_symbols(symbols, already_performed)

    for symbol in symbols:
        symbol_params_combinations = grouped_by_symbol[symbol]
        # Multithreading
        num_cores = multiprocessing.cpu_count()
        print('num_cores', num_cores)
        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            futures = []
            for i, combo in enumerate(symbol_params_combinations, start=1):
                futures.append(executor.submit(process_combination, combo, data_loader, nb_comb, i))

            df_results = pd.concat([future.result() for future in futures], ignore_index=True)

        # Save results
        desired_columns = [
            'pair', 'timeframe', 'param_set', 'wallet', 'sharpe_ratio',
            'win_rate', 'avg_profit', 'total_trades', 'max_drawdown',
            'trix_length', 'trix_signal_length', 'trix_signal_type', 'long_ma_length', 'size'
        ]
        df_results = df_results[desired_columns]
        modified_symbol = symbol.replace("/", "")
        if input_data.COLAB:
            dir_colab = '/content/drive/My Drive/Colab Notebooks/param_optimization/'
            path_dir_split_result = dir_colab + "split_results"
        else:
            path_dir_split_result = "./split_results"
        save_dataframe_with_unique_filename(df_results, base_filename=modified_symbol + "_results_test_multi", directory=path_dir_split_result)

    # End the timer
    end_time = time.time()

    # Calculate duration
    duration = end_time - start_time

    # Convert to h:m:s
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    print(f"Duration: {hours}h {minutes}m {seconds}s")


if __name__ == "__main__":
    asyncio.run(main())
