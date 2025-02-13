import os
import pandas as pd

import utils
from convert_to_xcel import convert_csv_for_excel
import shutil

def reorder_dataframe(df, column_order):
    """
    Reorders the columns of the dataframe based on the given column_order.

    Args:
    df (pd.DataFrame): The input dataframe.
    column_order (list): List of column names in the desired order.

    Returns:
    pd.DataFrame: Dataframe with columns rearranged.
    """
    # Ensure that only existing columns in df are used (to avoid missing column errors)
    existing_columns = [col for col in column_order if col in df.columns]
    return df[existing_columns]

def set_columns_upper(df):
    """
    Convert all column names of a dataframe to uppercase.

    Args:
    df (pd.DataFrame): Input dataframe.

    Returns:
    pd.DataFrame: Dataframe with uppercase column names.
    """
    df.columns = df.columns.str.upper()
    return df

def drop_columns_containing(df, substrings):
    """
    Drops columns from a dataframe if their name contains any string in the substrings list.

    :param df: Input dataframe
    :param substrings: List of substrings to check in column names
    :return: Dataframe with filtered columns
    """
    columns_to_drop = [col for col in df.columns if any(sub in col for sub in substrings)]
    return df.drop(columns=columns_to_drop)


def sort_dataframe_by_id(df):
    df["ID"] = df["ID"].astype(int)  # Convert ID column to integer
    return df.sort_values(by="ID", ascending=True)  # Change to False for descending order

def read_and_process_csv(file_path):
    """Reads the CSV file and adds 'outperform' and 'perf' columns."""
    df = pd.read_csv(file_path)

    df = sort_dataframe_by_id(df)
    df.reset_index(drop=True, inplace=True)

    # Function to clean percentage-based columns
    def clean_percentage(value):
        """Removes '%' and replaces ',' with '.' for correct conversion."""
        if isinstance(value, str):
            return value.replace('%', '').replace(',', '.')
        return value

    # Apply cleaning and conversion
    df['M_CUMULATIVE_RETURN'] = pd.to_numeric(df['M_CUMULATIVE_RETURN'].apply(clean_percentage), errors='coerce')
    df['M_BUY_HOLD_RETURN'] = pd.to_numeric(df['M_BUY_HOLD_RETURN'].apply(clean_percentage), errors='coerce')
    df['Total Return [%]'] = pd.to_numeric(df['Total Return [%]'].str.replace(',', '.', regex=True), errors='coerce')
    df['Benchmark Return [%]'] = pd.to_numeric(df['Benchmark Return [%]'].str.replace(',', '.', regex=True), errors='coerce')

    # Add 'outperform' column
    df['outperform'] = (df['M_CUMULATIVE_RETURN'] > df['M_BUY_HOLD_RETURN']) | \
                       (df['Total Return [%]'] > df['Benchmark Return [%]'])

    # Add 'perf' column (difference in percentage return)
    df['perf'] = df['Total Return [%]'] - df['Benchmark Return [%]']

    return df


def add_suffix_to_columns(df: pd.DataFrame, suffix: str) -> pd.DataFrame:
    """
    Append a suffix to all column names in a dataframe.

    :param df: The input dataframe
    :param suffix: The suffix to append to column names
    :return: A new dataframe with modified column names
    """
    df_renamed = df.copy()
    df_renamed.columns = [f"{col}_{suffix}" for col in df.columns]
    return df_renamed

def _merge_dataframes(df, df_reversed):
    """Merges df and df_reversed on 'ID' with renaming rules."""
    common_columns = ['ID', 'SYMBOL', 'TIMEFRAME', 'MA_TYPE', 'TREND_TYPE', 'LOW_TIMEFRAME', 'HIGH_TIMEFRAME',
                      'STOP_LOSS', 'FEES']

    # Rename df_reversed columns to have '_REVERSE' suffix for non-common columns
    rename_map = {col: f"{col}_REVERSE" for col in df_reversed.columns if col not in common_columns}
    df_reversed = df_reversed.rename(columns=rename_map)

    # Merge dataframes on 'ID'
    df_merge = df.merge(df_reversed, on='ID', how='inner')

    # Add 'overall_perf' column
    df_merge['OVERALL_PERF'] = df_merge['outperform'] & df_merge['outperform_REVERSE']

    # Convert column names to uppercase
    df_merge.columns = [col.upper() for col in df_merge.columns]

    return df_merge


def merge_dataframes(df_merge, df, df_reversed):
    """
    Merge three dataframes and arrange the columns in the required interleaved order.

    Args:
    df_merge (pd.DataFrame): First dataframe with any columns.
    df (pd.DataFrame): Second dataframe with any columns.
    df_reversed (pd.DataFrame): Third dataframe with any columns.

    Returns:
    pd.DataFrame: Merged dataframe with interleaved columns.
    """
    # Ensure all dataframes have the same number of rows
    if not (len(df_merge) == len(df) == len(df_reversed)):
        raise ValueError("All dataframes must have the same number of rows.")

    # Extract column names
    cols_merge = df_merge.columns.tolist()
    cols_df = df.columns.tolist()
    cols_reversed = df_reversed.columns.tolist()

    # Create the new column order by interleaving
    merged_columns = cols_merge
    for col_df, col_reversed in zip(cols_df, cols_reversed):
        merged_columns.extend([col_df, col_reversed])

    # Concatenate dataframes horizontally
    df_result = pd.concat([df_merge, df, df_reversed], axis=1)

    # Reorder columns dynamically
    df_result = df_result[merged_columns]

    return df_result


def copy_png_files(source_dir, destination_dir, prefix_list):
    """
    Copies all .png files from source_dir to destination_dir that start with a prefix in prefix_list.
    The prefixes are separated by "_" in the filename.

    :param source_dir: Directory where the .png files are located.
    :param destination_dir: Directory where the filtered .png files will be copied.
    :param prefix_list: List of prefixes to filter files.
    """
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    for filename in os.listdir(source_dir):
        if filename.endswith(".png"):
            parts = filename.split("_")
            if int(parts[0]) in prefix_list:  # Checking if the first part matches any prefix
                source_path = os.path.join(source_dir, filename)
                destination_path = os.path.join(destination_dir, filename)
                shutil.copy2(source_path, destination_path)
                print(f"Copied: {filename}")

    print("Copying process completed.")

def add_suffix_to_png_files(directory, suffix):
    """
    Adds a suffix to all .png files in the specified directory.

    Args:
        directory (str): The path to the directory containing .png files.
        suffix (str): The suffix to add before the file extension.

    Returns:
        None
    """
    for filename in os.listdir(directory):
        if filename.endswith(".png"):
            base_name, ext = os.path.splitext(filename)
            new_filename = f"{base_name}_{suffix}{ext}"
            old_path = os.path.join(directory, filename)
            new_path = os.path.join(directory, new_filename)
            os.rename(old_path, new_path)
            print(f"Renamed: {filename} → {new_filename}")

def copy_png(df):
    df["FEES"] = df["FEES"].astype(str).str.replace(",", ".").astype(float).astype(float)
    df_filtered = df[df["OVERALL_OUTPERFORM"] == True]
    df_no_fees = df_filtered[df_filtered["FEES"] == 0]
    df_w_fees = df_filtered[df_filtered["FEES"] != 0]

    lst_no_fees = df_no_fees["ID"].to_list()
    lst_w_fees = df_w_fees["ID"].to_list()

    dest_no_fee = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\selection\no_fees"
    dest_w_fee = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\selection\with_fees"
    source_up = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test"
    source_reverse = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend_reverse\result_test"

    if False:
        add_suffix_to_png_files(source_up, 'up')
        add_suffix_to_png_files(source_reverse, 'reversed')
    copy_png_files(source_up, dest_no_fee, lst_no_fees)
    copy_png_files(source_up, dest_w_fee, lst_w_fees)
    copy_png_files(source_reverse, dest_no_fee, lst_no_fees)
    copy_png_files(source_reverse, dest_w_fee, lst_w_fees)




def main(directory):
    """Main function to process files and save the final dataframe."""
    file1 = os.path.join(directory, "output_merged.csv")
    file2 = os.path.join(directory, "output_merged_reversed.csv")

    if not os.path.exists(file1) or not os.path.exists(file2):
        print("Error: One or both files are missing in the directory.")
        return

    substrings = [
        "Unnamed",
        "START_DATE",
        "END_DATE",
        "Start Index",
        "End Index",
        "Total Duration",
        "Start Value",
        "Position Coverage [%]",
        "Max Gross Exposure [%]",
        "Max Drawdown Duration",
        "Total Orders",
        "Avg Winning Trade Duration",
        "Avg Losing Trade Duration"
    ]

    df = read_and_process_csv(file1)
    df = drop_columns_containing(df, substrings)

    columns = [
        "ID",
        "SYMBOL",
        "TIMEFRAME",
        "MA_TYPE",
        "TREND_TYPE",
        "LOW_TIMEFRAME",
        "HIGH_TIMEFRAME",
        "STOP_LOSS",
        "FEES"
    ]
    df_merged = pd.DataFrame()
    for col in columns:
        df_merged[col] = df[col]
    df = drop_columns_containing(df, columns)

    df = add_suffix_to_columns(df, "up")

    df_reversed = read_and_process_csv(file2)
    df_reversed = drop_columns_containing(df_reversed, substrings)
    df_reversed = drop_columns_containing(df_reversed, columns)
    df_reversed = add_suffix_to_columns(df_reversed, "reversed")

    df_merge = merge_dataframes(df_merged, df, df_reversed)
    df_merge["overall_outperform"] = df_merge['outperform_up'] & df_merge['outperform_reversed']

    input_data_full = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\selection\input_data_full.csv"
    df_input = pd.read_csv(input_data_full)
    df_input = set_columns_upper(df_input)
    df_input = sort_dataframe_by_id(df_input)

    lst_params = ['HIGH_OFFSET', 'LOW_OFFSET', 'ZEMA_LEN_BUY', 'ZEMA_LEN_SELL', 'SSL_ATR_PERIOD']
    for param in lst_params:
        df_merge[param] = df_input[param]

    df_merge = set_columns_upper(df_merge)

    column_order = [
        "ID", "SYMBOL", "TIMEFRAME", "MA_TYPE", "TREND_TYPE", "LOW_TIMEFRAME", "HIGH_TIMEFRAME",
        'HIGH_OFFSET', 'LOW_OFFSET', 'ZEMA_LEN_BUY', 'ZEMA_LEN_SELL', 'SSL_ATR_PERIOD',
        "STOP_LOSS", "FEES", "OUTPERFORM_UP", "OUTPERFORM_REVERSED", "OVERALL_OUTPERFORM",
        "M_CUMULATIVE_RETURN_UP", "M_CUMULATIVE_RETURN_REVERSED", "M_BUY_HOLD_RETURN_UP",
        "M_BUY_HOLD_RETURN_REVERSED",
        "TOTAL RETURN [%]_UP", "TOTAL RETURN [%]_REVERSED",
        "BENCHMARK RETURN [%]_UP", "BENCHMARK RETURN [%]_REVERSED",
        "PERF_UP", "PERF_REVERSED",
        "M_WIN_RATE_UP", "M_WIN_RATE_REVERSED", "M_NUM_TRADES_UP", "M_NUM_TRADES_REVERSED",
        "M_MAX_DRAWDOWN_UP", "M_MAX_DRAWDOWN_REVERSED",
        "M_AVG_WIN_UP", "M_AVG_WIN_REVERSED", "M_AVG_LOSS_UP", "M_AVG_LOSS_REVERSED",
        "M_BEST_TRADE_UP", "M_BEST_TRADE_REVERSED", "M_WORST_TRADE_UP", "M_WORST_TRADE_REVERSED",
        "MIN VALUE_UP", "MIN VALUE_REVERSED", "MAX VALUE_UP", "MAX VALUE_REVERSED",
        "END VALUE_UP", "END VALUE_REVERSED", "MAX DRAWDOWN [%]_UP",
        "MAX DRAWDOWN [%]_REVERSED", "TOTAL FEES PAID_UP", "TOTAL FEES PAID_REVERSED",
        "TOTAL TRADES_UP", "TOTAL TRADES_REVERSED", "WIN RATE [%]_UP", "WIN RATE [%]_REVERSED",
        "BEST TRADE [%]_UP", "BEST TRADE [%]_REVERSED", "WORST TRADE [%]_UP", "WORST TRADE [%]_REVERSED",
        "AVG WINNING TRADE [%]_UP", "AVG WINNING TRADE [%]_REVERSED", "AVG LOSING TRADE [%]_UP",
        "AVG LOSING TRADE [%]_REVERSED", "PROFIT FACTOR_UP", "PROFIT FACTOR_REVERSED",
        "EXPECTANCY_UP", "EXPECTANCY_REVERSED", "SHARPE RATIO_UP", "SHARPE RATIO_REVERSED",
        "CALMAR RATIO_UP", "CALMAR RATIO_REVERSED", "OMEGA RATIO_UP", "OMEGA RATIO_REVERSED",
        "SORTINO RATIO_UP", "SORTINO RATIO_REVERSED", "M_FINAL_BALANCE_UP", "M_FINAL_BALANCE_REVERSED"
    ]
    df_merge = reorder_dataframe(df_merge, column_order)

    output_file = os.path.join(directory, "final_output.csv")
    df_merge.to_csv(output_file, index=False)
    print(f"Final merged file saved to: {output_file}")

    new_excel_path = utils.add_exel_before_csv(output_file)
    convert_csv_for_excel(output_file, new_excel_path)

    return df_merge

if __name__ == "__main__":
    input_directory = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\selection"
    df_merge = main(input_directory)
    copy_png(df_merge)
