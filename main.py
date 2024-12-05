import pandas as pd

if __name__ == '__main__':
    file_path = './results/results_test_multi_0004.csv'
    dir_output = 'output_full/'

    # Step 1: Read the CSV files and merge
    df = pd.read_csv(file_path)
    if False:
        file_path = './results/results_02.csv'
        df_02 = pd.read_csv(file_path)
        df = pd.concat([df, df_02], ignore_index=True)

    # Reindex after merge
    df.reset_index(drop=True, inplace=True)

    # Save the merged DataFrame
    file_path = './results/results_01_02.csv'
    df.to_csv(file_path)

    # Step 2: Normalize Columns
    df["wallet_normalized"] = df["wallet"] / df["wallet"].max()
    df["win_rate_normalized"] = df["win_rate"] / df["win_rate"].max()
    df["sharpe_ratio_normalized"] = df["sharpe_ratio"] / df["sharpe_ratio"].max()
    df["avg_profit_normalized"] = df["avg_profit"] / df["avg_profit"].max()
    df["max_drawdown_normalized"] = (100 + df["max_drawdown"]) / (100 + df["max_drawdown"].max())

    # Step 3: Calculate Rank (Simple Rank)
    df["rank_score"] = (
        df["wallet_normalized"]
        + df["win_rate_normalized"]
        + df["sharpe_ratio_normalized"]
        + df["avg_profit_normalized"]
        + df["max_drawdown_normalized"]
    )

    # Step 4: Calculate Weighted Rank
    weights = {
        "wallet_normalized": 2,
        "win_rate_normalized": 1,
        "sharpe_ratio_normalized": 2,
        "avg_profit_normalized": 1,
        "max_drawdown_normalized": 1
    }
    df["weighted_rank_score"] = (
        df["wallet_normalized"] * weights["wallet_normalized"]
        + df["win_rate_normalized"] * weights["win_rate_normalized"]
        + df["sharpe_ratio_normalized"] * weights["sharpe_ratio_normalized"]
        + df["avg_profit_normalized"] * weights["avg_profit_normalized"]
        + df["max_drawdown_normalized"] * weights["max_drawdown_normalized"]
    )

    # Step 5: Convert Scores to Ranks
    df["rank"] = df["rank_score"].rank(ascending=False).astype(int)
    df["weighted_rank"] = df["weighted_rank_score"].rank(ascending=False).astype(int)

    # Step 6: Drop Unnecessary Columns
    columns_to_drop = [
        "param_set", "size", "wallet_normalized",
        "win_rate_normalized", "sharpe_ratio_normalized",
        "avg_profit_normalized", "max_drawdown_normalized", "rank_score", "weighted_rank_score"
    ]
    df = df.drop(columns=columns_to_drop, errors="ignore")

    # Save the Intermediate DataFrame
    intermediate_file = './results/intermediate_dataframe.csv'
    df.to_csv(intermediate_file, index=False)
    print(f"Intermediate DataFrame saved to {intermediate_file}")

    # Step 7: Create a new DataFrame with the top 5 of each group
    grouped = df.groupby(['pair', 'timeframe'], group_keys=False)
    top_5_rank = grouped.apply(lambda x: x.nsmallest(5, 'rank'))
    top_5_weighted_rank = grouped.apply(lambda x: x.nsmallest(5, 'weighted_rank'))
    top_5_combined = pd.concat([top_5_rank, top_5_weighted_rank]).drop_duplicates().reset_index(drop=True)

    # Create a new DataFrame with the top 1 of each group
    top_1_rank = grouped.apply(lambda x: x.nsmallest(1, 'rank'))
    top_1_weighted_rank = grouped.apply(lambda x: x.nsmallest(1, 'weighted_rank'))
    top_1_combined = pd.concat([top_1_rank, top_1_weighted_rank]).drop_duplicates().reset_index(drop=True)

    # Save the Final DataFrames
    top_5_combined.to_csv('./results/top_5_per_pair_timeframe.csv', index=False)
    top_1_combined.to_csv('./results/top_1_per_pair_timeframe.csv', index=False)
    print("Top 5 and Top 1 DataFrames saved.")

    # Step 8: Calculate Recurrence Percentages for Parameters
    def calculate_recurrence(df, group_by, parameters):
        # Group by the specified columns + parameters and count occurrences
        counts = df.groupby(group_by + parameters).size()

        # Group by the base grouping (e.g., "pair") and calculate total counts
        total_counts = counts.groupby(level=group_by).transform("sum")

        # Calculate percentages
        percentages = (counts / total_counts) * 100

        # Reset index to convert grouped columns back to regular columns
        result = percentages.reset_index(name="percentage")

        return result


    parameters = ["trix_length", "trix_signal_length", "trix_signal_type", "long_ma_length"]

    # Recurrence per pair
    pair_recurrence = calculate_recurrence(df, ["pair"], parameters)
    pair_recurrence.to_csv('./results/pair_recurrence.csv', index=False)

    # Recurrence per timeframe
    timeframe_recurrence = calculate_recurrence(df, ["timeframe"], parameters)
    timeframe_recurrence.to_csv('./results/timeframe_recurrence.csv', index=False)

    # Recurrence per pair/timeframe combination
    pair_timeframe_recurrence = calculate_recurrence(df, ["pair", "timeframe"], parameters)
    pair_timeframe_recurrence.to_csv('./results/pair_timeframe_recurrence.csv', index=False)

    print("Recurrence DataFrames saved.")

    # Print Previews
    print("Pair Recurrence:")
    print(pair_recurrence.head())
    print("\nTimeframe Recurrence:")
    print(timeframe_recurrence.head())
    print("\nPair/Timeframe Recurrence:")
    print(pair_timeframe_recurrence.head())
