import os
import sys
import pandas as pd
import utils
import threading
from convert_to_xcel import convert_csv_for_excel

def list_csv_files(input_dir: str) -> list:
    """
    Lists all CSV files in the specified directory.

    :param input_dir: Path to the directory containing CSV files.
    :return: A list of full paths to CSV files.
    """
    csv_files = []

    # List all files in the directory
    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith('.csv'):
            full_path = os.path.join(input_dir, file_name)
            csv_files.append(full_path)

    return csv_files


def merge_and_remove_duplicates(csv_files: list) -> pd.DataFrame:
    """
    Reads and merges all CSV files into a single DataFrame,
    then removes duplicate rows.

    :param csv_files: A list of full paths to CSV files.
    :return: A pandas DataFrame containing merged data without duplicates.
    """
    dataframes = []

    for f in csv_files:
        separator = utils.detect_delimiter(f)
        # Check for the keyword in the filename (case-insensitive)
        df = pd.read_csv(f, sep=separator)
        dataframes.append(df)

    if not dataframes:
        print("No CSV files found. Returning an empty DataFrame.")
        return pd.DataFrame()

    # Concatenate and remove duplicates
    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df.drop_duplicates(inplace=True)

    return merged_df


def save_merged_csv(df: pd.DataFrame, output_path: str) -> None:
    """
    Saves the DataFrame to a CSV file at the specified path.

    :param df: The pandas DataFrame to be saved.
    :param output_path: The path (including filename) where the CSV will be saved.
    """
    df.to_csv(output_path, index=False)
    print(f"Data saved to: {output_path}")

    duplicated_ids_list = df["ID"][df["ID"].duplicated(keep=False)].unique().tolist()

    # Print the list
    print("Duplicated IDs list:", duplicated_ids_list)

def main():
    """
    Main function that orchestrates listing CSV files, merging them,
    removing duplicates, and saving the final CSV.

    Expected usage:
      python merge_csv.py <input_directory> <output_csv_file>
    """
    if False:
        input_dir = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\run_failed\exel"
        output_csv = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\run_failed\exel\output_merged.csv"
        filtered_output_csv = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\run_failed\exel\output_merged_filtered.csv"
    else:
        input_dir = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend_reverse\result_test\run_failed\exel"
        output_csv = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend_reverse\result_test\run_failed\exel\output_merged.csv"
        filtered_output_csv = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend_reverse\result_test\run_failed\exel\output_merged_filtered.csv"

    # 1. List all CSV files
    csv_files = list_csv_files(input_dir)

    # 2. Merge them and remove duplicates
    merged_df = merge_and_remove_duplicates(csv_files)



    # 1. Convert END_DATE to datetime
    # merged_df["END_DATE"] = pd.to_datetime(merged_df["END_DATE"], errors='coerce')
    merged_df["END_DATE"] = merged_df["END_DATE"].str.replace(",", ".", regex=False)
    merged_df["END_DATE"] = pd.to_datetime(merged_df["END_DATE"], format="%Y-%m-%d %H:%M:%S.%f%z")

    # 2. Sort the DataFrame by END_DATE
    df_sorted = merged_df.sort_values(by="END_DATE")
    # df_sorted = merged_df.sort_values(by="M_CUMULATIVE_RETURN")

    # 3. Drop duplicates based on ID, keeping the last (the one with the max END_DATE)
    df_latest = df_sorted.drop_duplicates(subset="ID", keep="last")

    merged_df = df_latest

    # 3. Save the merged DataFrame to the output path
    save_merged_csv(merged_df, output_csv)

    new_excel_path = utils.add_exel_before_csv(output_csv)
    convert_csv_for_excel(output_csv, new_excel_path)

    # List of columns to keep in the desired order
    columns_to_keep = [
        "ID", "SYMBOL", "TIMEFRAME", "MA_TYPE", "TREND_TYPE", "LOW_TIMEFRAME", "HIGH_TIMEFRAME",
        "STOP_LOSS", "FEES", "Sharpe Ratio", "M_FINAL_BALANCE", "M_CUMULATIVE_RETURN",
        "Total Return [%]", "M_BUY_HOLD_RETURN", "Benchmark Return [%]", "M_WIN_RATE",
        "Win Rate [%]", "M_MAX_DRAWDOWN", "Max Drawdown [%]", "M_NUM_TRADES", "Total Orders",
        "M_AVG_WIN", "M_AVG_LOSS", "M_BEST_TRADE", "M_WORST_TRADE", "Min Value", "Max Value",
        "End Value", "Total Fees Paid", "Total Trades", "Best Trade [%]", "Worst Trade [%]",
        "Avg Winning Trade [%]", "Avg Losing Trade [%]", "Avg Winning Trade Duration",
        "Avg Losing Trade Duration", "Expectancy", "Calmar Ratio", "Omega Ratio", "Sortino Ratio"
    ]
    # Keep only the specified columns in the desired order
    df_filtered = merged_df[columns_to_keep]

    # 3. Save the merged DataFrame to the output path
    save_merged_csv(df_filtered, filtered_output_csv)

    new_excel_path = utils.add_exel_before_csv(filtered_output_csv)
    convert_csv_for_excel(filtered_output_csv, new_excel_path)

if __name__ == "__main__":
    main()
