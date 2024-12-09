import asyncio
import itertools
from concurrent.futures import ThreadPoolExecutor
import multiprocessing
from utilities.data_manager import ExchangeDataManager
from utilities.custom_indicators import Trix, TrixVBT
from utilities.my_utils import compare_multiindex_levels
from utilities.bt_analysis import get_metrics
from utilities.plot_analysis import plot_equity_vs_asset, plot_bar_by_month
import ta
import pandas as pd
import platform
from utilities.my_utils import save_dataframe_with_unique_filename, extract_symbols_from_files, remove_performed_symbols
from vectorbtpro import *
from collections import defaultdict

import input_data

import time


def RSI(data):
    # data.get("Close")["BTCUSDT"].plot().show()

    open_price = data.get('Open')
    close_price = data.get('Close')
    rsi = vbt.RSI.run(open_price)
    entries = rsi.rsi.vbt.crossed_below(30)
    exits = rsi.rsi.vbt.crossed_above(70)

    # clean_entries.vbt.signals.total()
    # clean_exits.vbt.signals.total()

    """
    pf = vbt.Portfolio.from_signals(
        close=close_price,
        entries=entries,
        exits=exits,
        size=100,
        size_type='value',
        init_cash='auto'
    )

    pf.stats()
    """

    return entries, exits

class Strategy:
    def __init__(self, symbols, tf, vbt_data, strategy_type, params):
        self.symbols = symbols
        self.tf = tf
        self.vbt_data = vbt_data
        self.side = strategy_type,
        self.use_long = "long" in strategy_type
        self.use_short = "short" in strategy_type
        self.params = params

    def populate_indicators(self):
        # Populate indicators
        self.trix_obj = TrixVBT(
            vbt_data=self.vbt_data,
            trix_length=self.params["trix_length"],
            trix_signal_length=self.params["trix_signal_length"],
            trix_signal_type=self.params["trix_signal_type"],
            long_ma_length=self.params["long_ma_length"]
        )

    def populate_buy_sell(self):
        self.open_long = self.trix_obj.get_trix_histo().vbt.crossed_above(0) \
                         & self.vbt_data.get("Close").vbt.crossed_above(self.trix_obj.get_long_ma())
        # self.open_long = self.trix_obj.get_trix_histo().vbt.crossed_above(0)
        self.close_long = self.trix_obj.get_trix_histo().vbt.crossed_below(0)

        # self.open_long = ((self.trix_obj.get_trix_histo() > 0) & (self.vbt_data.get("Close") > self.trix_obj.get_long_ma())).astype(int)
        # self.close_long = (self.trix_obj.get_trix_histo() < 0).astype(int)

        # self.open_short = ((self.trix_obj.get_trix_histo() < 0) & (self.vbt_data.get("Close") < self.trix_obj.get_long_ma())).astype(int)
        # self.close_short = (self.trix_obj.get_trix_histo() > 0).astype(int)


    def run_backtest(self, initial_wallet=1000, leverage=1, start_date=None, end_date=None):
        lst_results = []
        close = self.vbt_data.get("Close")
        signal_open_long = self.open_long
        signal_close_long = self.close_long
        # signal_open_long = self.open_long == 1
        # signal_close_long = self.close_long == 1

        # for symbol in self.symbols:
            # close = self.vbt_data.get("Close")[symbol]
            # signal_open_long = self.open_long[symbol] == 1
            #signal_close_long = self.close_long[symbol] == 1

        close = self.vbt_data.get("Close")
        signal_open_long = self.open_long
        signal_close_long = self.close_long

        # Set frequency dynamically based on timeframe
        frequency_mapping = {
            '1m': '1T',  # 1 minutes
            '5m': '5T',  # 5 minutes
            '15m': '15T',  # 15 minutes
            '30m': '30T',  # 30 minutes
            '1h': '1H',  # 1 hour
            '2h': '2H',  # 2 hours
        }
        freq = frequency_mapping.get(self.tf, None)

        pf = vbt.PF.from_signals(
            close=close,
            entries=signal_open_long,
            exits=signal_close_long,
            freq=freq,
            direction="longonly",
            size=1.0,
            size_type="percent",
            init_cash=10000,
            fees=0.001
        )
        for symbol in self.symbols:
            lst_results.append(
                {
                    "symbol": symbol,
                    "timeframe": self.tf,
                    "side": self.side[0],
                    "trix_length": self.params["trix_length"],
                    "trix_signal_length": self.params["trix_signal_length"],
                    "trix_signal_type": self.params["trix_signal_type"],
                    "long_ma_length": self.params["long_ma_length"],
                    **pf[symbol].stats().to_dict()  # Unpack the stats dictionary into the main dictionary
                }
            )

        return lst_results
