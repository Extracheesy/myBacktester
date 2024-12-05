import pandas as pd
import itertools
from utilities.data_manager import ExchangeDataManager
from utilities.custom_indicators import Trix
from utilities.bt_analysis import get_metrics
from utilities.plot_analysis import plot_equity_vs_asset, plot_bar_by_month
import ta


class DataLoader:
    def __init__(self, exchange_name, path_download):
        self.exchange = ExchangeDataManager(exchange_name=exchange_name, path_download=path_download)

    def load_data(self, pair, timeframe):
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
        if start_date or end_date:
            self.df_list = {
                k: v[(v.index >= start_date) & (v.index <= end_date)]
                for k, v in self.df_list.items()
            }
        params = self.params
        df_ini = self.df_list[self.oldest_pair]
        wallet = initial_wallet
        trades, days = [], []

        for index, row in df_ini.iterrows():
            # Backtesting logic

            # Populate daily summary
            days.append({"day": index.date(), "wallet": wallet})

        return {"wallet": wallet, "trades": pd.DataFrame(trades), "days": pd.DataFrame(days)}


class MultiParamStrategy:
    def __init__(self, data_loader, trading_pairs, timeframes, params_combinations):
        self.data_loader = data_loader
        self.trading_pairs = trading_pairs
        self.timeframes = timeframes
        self.params_combinations = params_combinations

    def run(self, initial_wallet, leverage, start_date, end_date):
        results = []
        for combo in self.params_combinations:
            df_list = {}
            params = {}

            for tf, pair, param in combo:
                df = self.data_loader.load_data(pair, tf)
                df["pair"] = pair
                df["tf"] = tf
                df_list[f"{tf}-{pair}"] = df
                params[f"{tf}-{pair}"] = param

            oldest_pair = next(iter(df_list))
            strategy = Strategy(df_list, oldest_pair, ["long"], params)
            strategy.populate_indicators()
            strategy.populate_buy_sell()
            result = strategy.run_backtest(initial_wallet, leverage, start_date, end_date)
            results.append(result)

        return results
