# !/usr/bin/env python3

import os
import sys
import re


def get_numeric_prefixes(directory_path):
    """
    Parses all .csv files in the given directory and extracts
    any filename prefixes of the form 'digits_' (e.g. '123_').

    :param directory_path: Path to the directory containing the CSV files.
    :return: A list of matching prefixes (strings like '123_').
    """
    # Regex pattern to match filenames beginning with one or more digits
    # followed by an underscore, and ending with '.csv'
    pattern = re.compile(r'^(\d+_)')

    prefixes = []

    # List all files in the given directory
    for filename in os.listdir(directory_path):
        # We're only interested in CSV files
        if filename.lower().endswith('.png'):
            match = pattern.match(filename)
            if match:
                prefix_without_underscore = match.group(1).replace('_', '')
                prefixes.append(prefix_without_underscore)

    return prefixes


def drop_rows_by_id(df, id_list):
    """
    Drops all rows in the DataFrame df where df['ID'] is in id_list.

    Parameters:
    df (pd.DataFrame): The input DataFrame, which must have an "ID" column.
    id_list (list): List of IDs to remove from df.

    Returns:
    pd.DataFrame: A new DataFrame with rows removed where ID was in id_list.
    """
    # Keep only those rows where 'ID' is NOT in id_list
    filtered_df = df[~df["ID"].isin(id_list)]

    # Optionally, you can use .copy() if you want a completely independent DataFrame
    # filtered_df = df[~df["ID"].isin(id_list)].copy()

    return filtered_df

def main():
    directory_path = r"C:\Users\INTRADE\PycharmProjects\Analysis\ObelixParam\test_multi_trend\result_test\run_2_failed"

    # Get the list of prefixes
    result = get_numeric_prefixes(directory_path)

    # Print out the result
    print("Found prefixes:", result)


if __name__ == "__main__":
    main()
