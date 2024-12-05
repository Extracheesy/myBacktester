import asyncio
import itertools
from utilities.data_manager import ExchangeDataManager
from utilities.custom_indicators import Trix
from utilities.bt_analysis import get_metrics
from utilities.data_manager import ExchangeDataManager
from utilities.custom_indicators import get_n_columns, Trix
from utilities.bt_analysis import get_metrics, backtest_analysis
from utilities.plot_analysis import plot_equity_vs_asset, plot_futur_simulations, plot_bar_by_month
import ta
import pandas as pd
import platform
from utilities.my_utils import save_dataframe_with_unique_filename


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

    def explore_data(self):
        """Explore data."""
        self.exchange.explore_data()

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


async def main():
    # Start the timer
    start_time = time.time()

    # Initialize DataLoader
    exchange_name = "binance"
    path_download = "./database/exchanges"
    data_loader = DataLoader(exchange_name=exchange_name, path_download=path_download)

    df_results = None

    # Define coins and intervals
    coins_to_download = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    coins_to_download = ["BTC/USDT", "ETH/USDT"]
    intervals = ["1h", "2h", "4h"]
    intervals = ["1h"]

    # Download data
    await data_loader.download_data(coins=coins_to_download, intervals=intervals)
    data_loader.explore_data()

    # Strategy parameters
    trading_pairs = coins_to_download
    timeframes = intervals
    trix_lengths = [7, 11, 15, 20]
    trix_signal_lengths = [7, 11, 15, 20]
    trix_signal_types = ["sma", "ema"]
    long_ma_lengths = [200, 300, 500]

    trix_lengths = [7]
    trix_signal_lengths = [7]
    trix_signal_types = ["sma", "ema"]
    long_ma_lengths = [200]
    trix_size = [1]

    combinations = list(itertools.product(
        timeframes, trading_pairs,
        itertools.product(trix_lengths, trix_signal_lengths, trix_signal_types, long_ma_lengths, trix_size)
    ))

    params_combinations = [
        (tf, pair, {"trix_length": trix[0], "trix_signal_length": trix[1],
                    "trix_signal_type": trix[2], "long_ma_length": trix[3],
                    "size":trix[4]})
        for tf, pair, trix in combinations
    ]

    # Run strategy
    lst_results = []
    nb_comb = cpt = len(params_combinations)
    print("total combinations: ", cpt)
    for combo in params_combinations:
        print("remaining: ", cpt, " / ", nb_comb)
        cpt -= 1
        tf, pair, params = combo
        df = data_loader.load_data(pair, tf)
        df["pair"] = pair
        df["tf"] = tf
        df_list = {f"{tf}-{pair}": df}
        strategy = Strategy(df_list, f"{tf}-{pair}", ["long"], {f"{tf}-{pair}": params})
        strategy.populate_indicators()
        strategy.populate_buy_sell()
        dct_result = strategy.run_backtest(initial_wallet=1000, leverage=1, start_date="2020-01-01", end_date=None)
        lst_results.append(dct_result)

        # Fields to exclude from bt_result
        exclude_fields = {'trades', 'days'}
        # Filter bt_result to exclude specified fields
        filtered_bt_result = {k: v for k, v in dct_result.items() if k not in exclude_fields}

        param_set = "p1"
        # params = params[tf][param_set][pair]
        combined_data = {
            'timeframe': tf,
            'param_set': param_set,
            'pair': pair,
            **params,
            **filtered_bt_result
        }

        new_row = pd.DataFrame([combined_data])
        if df_results is None:
            df_results = new_row
        else:
            df_results = pd.concat([df_results, new_row], ignore_index=True)

        plot = False
        if plot:
            df_trades, df_days = backtest_analysis(
                trades=df_results["trades"],
                days=df_results["days"],
                general_info=True,
                trades_info=True,
                days_info=True,
                long_short_info=True,
                entry_exit_info=True,
                exposition_info=False,
                pair_info=True,
                indepedant_trade=True,
            )

            plot_equity_vs_asset(df_days=df_days.loc[:])
            df_trades
            plot_bar_by_month(df_days=df_days)

            from utilities.plot_analysis import plot_train_test_simulation
            plot_train_test_simulation(df_trades, "2023-09-10", 2, 1000)

    desired_columns = [
        'pair', 'timeframe', 'param_set', 'wallet', 'sharpe_ratio',
        'win_rate', 'avg_profit', 'total_trades', 'max_drawdown',
        'trix_length', 'trix_signal_length',
        'trix_signal_type', 'long_ma_length', 'size'
    ]

    # Reordering the DataFrame
    df_results = df_results[desired_columns]

    # Display the reordered DataFrame
    # df_results.to_csv("results.csv")
    save_dataframe_with_unique_filename(df_results, base_filename="results_test", directory="results")

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
