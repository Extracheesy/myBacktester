import os
import pandas as pd


def save_dataframe_with_unique_filename(df, base_filename, directory):
    """
    Save a DataFrame to a CSV file with a unique filename in the specified directory.

    Parameters:
    - df (pd.DataFrame): The DataFrame to save.
    - base_filename (str): The base name for the file (e.g., "results").
    - directory (str): The directory where the file should be saved.

    Returns:
    - str: The full path to the saved file.
    """
    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)

    # Generate a unique filename
    extension = ".csv"
    file_index = 1

    # Construct the filename and increment if it already exists
    while os.path.exists(os.path.join(directory, f"{base_filename}_{file_index:04d}{extension}")):
        file_index += 1

    unique_filename = os.path.join(directory, f"{base_filename}_{file_index:04d}{extension}")

    # Save the DataFrame
    df.to_csv(unique_filename, index=False)

    print(f"DataFrame saved to {unique_filename}")
    return unique_filename


def analyze_list_pairs(lst_pair):
    """
    Analyzes a list of lists to find common values and missing values in each list.

    Parameters:
        lst_pair (list of lists): Input list of lists to analyze.

    Returns:
        dict: A dictionary containing:
            - 'common_values': List of values common to all sublists.
            - 'missing_values': Dictionary of missing values for each list.
    """
    # Find common values (intersection of all lists)
    common_values = list(set.intersection(*map(set, lst_pair)))

    # Create a set of all unique values across all lists
    complete_set = set().union(*lst_pair)

    # Find missing values in each sublist, excluding empty sets
    missing_values = {
        index: list(complete_set - set(sublist))
        for index, sublist in enumerate(lst_pair)
        if complete_set - set(sublist)
    }

    return {
        'common_values': sorted(common_values),
        'missing_values': missing_values
    }

def extract_symbols_from_files(directory):
    """
    Extracts symbols from filenames in a given directory and converts them to the "BTC/USDT" format.

    Args:
        directory (str): The path to the directory containing the files.

    Returns:
        list: A list of symbols in the "BTC/USDT" format, or an empty list if the directory does not exist.
    """
    if not os.path.exists(directory):
        return []  # Return an empty list if the directory does not exist

    symbols = []
    for filename in os.listdir(directory):
        # Check if the filename matches the expected pattern
        if filename.endswith(".csv") and "_results_test_multi_" in filename:
            # Extract the symbol (e.g., "BTCUSDT" from "BTCUSDT_results_test_multi_0001.csv")
            symbol = filename.split("_results_test_multi_")[0]
            # Convert "BTCUSDT" to "BTC/USDT"
            formatted_symbol = f"{symbol[:-4]}/{symbol[-4:]}"
            symbols.append(formatted_symbol)
    return symbols

def remove_performed_symbols(symbols, already_performed):
    """
    Removes symbols that are already performed from the symbols list.

    Args:
        symbols (list): List of all symbols.
        already_performed (list): List of symbols that are already performed.

    Returns:
        list: Updated symbols list with items from already_performed removed.
    """
    return [symbol for symbol in symbols if symbol not in already_performed]

def compare_multiindex_levels(df1, df2):
    """
    Compare the MultiIndex levels of two DataFrames.

    Parameters:
    df1 (pd.DataFrame): First DataFrame.
    df2 (pd.DataFrame): Second DataFrame.

    Returns:
    bool: True if both DataFrames have identical MultiIndex levels, False otherwise.
    """
    # Check if both DataFrames have MultiIndex
    if not isinstance(df1.index, pd.MultiIndex):
        print("One or both DataFrames do not have a MultiIndex.")
        return False
    if not isinstance(df2.index, pd.MultiIndex):
        print("One or both DataFrames do not have a MultiIndex.")
        return False
    if not isinstance(df1.index, pd.MultiIndex) or not isinstance(df2.index, pd.MultiIndex):
        print("One or both DataFrames do not have a MultiIndex.")
        return False

    # Compare the number of levels
    if df1.index.nlevels != df2.index.nlevels:
        print("The number of levels in the MultiIndex differ.")
        return False

    # Compare level names
    if df1.index.names != df2.index.names:
        print("The names of the levels in the MultiIndex differ.")
        return False

    # Compare unique values in each level
    for level in df1.index.names:
        df1_level_values = df1.index.get_level_values(level).unique()
        df2_level_values = df2.index.get_level_values(level).unique()
        if not df1_level_values.equals(df2_level_values):
            print(f"The unique values in the level '{level}' differ.")
            return False

    # If all checks pass
    return True
