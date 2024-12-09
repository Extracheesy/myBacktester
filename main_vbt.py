from data_loader import DataLoaderVBT
from utilities.custom_indicators import TrixVBT
from vbt_strategy_trix import Strategy
from vectorbtpro import *
import itertools
from collections import defaultdict
from utilities.my_utils import save_dataframe_with_unique_filename, extract_symbols_from_files, remove_performed_symbols
import input_data
import time
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def process_combination(combo, vbt_data, nb_comb, current_index):
    tf, pair, params = combo
    print(f"Processing combination {current_index}/{nb_comb}...")

    symbols = list(vbt_data.columns)

    strategy = Strategy(symbols, tf, vbt_data, ["long"], params)
    strategy.populate_indicators()
    strategy.populate_buy_sell()
    combined_data = strategy.run_backtest(initial_wallet=1000, leverage=1, start_date="2020-01-01", end_date=None)

    return pd.DataFrame(combined_data)

if __name__ == '__main__':
    run_start_time = time.time()

    # Define parameters
    symbols = input_data.lst_coin
    start_date = input_data.start_date
    end_date = input_data.end_date
    intervals = input_data.timeframes
    trix_lengths = input_data.trix_lengths
    trix_signal_lengths = input_data.trix_signal_lengths
    trix_signal_types = input_data.trix_signal_types
    long_ma_lengths = input_data.long_ma_lengths
    trix_size = input_data.size

    str_coins_to_download = '-'.join(symbols)
    combinations = list(itertools.product(
        intervals, [str_coins_to_download],
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
        tf, symbol, params = item
        grouped_by_symbol[tf].append(item)

    # Get a list of unique symbols
    tf = list(grouped_by_symbol.keys())
    # already_performed = extract_symbols_from_files("split_vbt_results")
    # already_performed = extract_tf_from_files("split_vbt_results")
    already_performed = []
    tf = remove_performed_symbols(symbols, already_performed)

    for tf in intervals:
        dataLoaderVBT = DataLoaderVBT(start_date, end_date, "vbt_data")
        vbt_data = dataLoaderVBT.fetch_data(symbols, tf).loc[start_date:]

        str_symbols = '-'.join(symbols)
        vbt_data_list = {f"{tf}-{str_symbols}": vbt_data}

        symbol_params_combinations = grouped_by_symbol[tf]
        # Multithreading
        num_cores = multiprocessing.cpu_count()
        print('num_cores', num_cores)

        with ThreadPoolExecutor(max_workers=num_cores) as executor:
            futures = []
            for i, combo in enumerate(symbol_params_combinations, start=1):
                futures.append(executor.submit(process_combination, combo, vbt_data, nb_comb, i))

            df_results = pd.concat([future.result() for future in futures], ignore_index=True)

    save_dataframe_with_unique_filename(df_results, "vbt_test_results", "vbt_test_results")

    # End the timer
    end_time = time.time()

    # Calculate duration
    duration = end_time - run_start_time

    # Convert to h:m:s
    hours = int(duration // 3600)
    minutes = int((duration % 3600) // 60)
    seconds = int(duration % 60)
    print(f"Duration: {hours}h {minutes}m {seconds}s")



