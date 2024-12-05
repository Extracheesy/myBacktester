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