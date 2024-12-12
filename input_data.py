def create_range_list(A, B, x):
    """
    Create a list with values from A to B with a step size of x.

    Parameters:
    A (float): Start of the range.
    B (float): End of the range.
    x (float): Step size.

    Returns:
    list: A list containing the range values.
    """
    if A > B and x > 0:
        raise ValueError("Step size x must be negative for a descending range.")
    elif A < B and x < 0:
        raise ValueError("Step size x must be positive for an ascending range.")

    range_list = []
    current_value = A
    if A <= B:  # Ascending range
        while current_value <= B:
            range_list.append(current_value)
            current_value += x
    else:  # Descending range
        while current_value >= B:
            range_list.append(current_value)
            current_value += x  # x should be negative

    return range_list


___lst_coin = [
    "KASUSDT",
    "BTCUSDT", #
    "ETHUSDT",
    "SOLUSDT", #
    ]

lst_coin = [
    "KASUSDT",
    "HBARUSDT",
    "FLOKIUSDT",
    "WIFUSDT",
    "INJUSDT",
    "VETUSDT",
    "AAVEUSDT",
    "TAOUSDT",
    "BONKUSDT",
    "RENDERUSDT",
    "BTCUSDT", #
    "ETHUSDT",
    "SOLUSDT", #
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "TRXUSDT",
    "SHIBUSDT",
    "TONUSDT",
    "SUIUSDT",
    "PEPEUSDT",
    "XLMUSDT",
    "NEARUSDT",
    # "ADAUSDT",
    # "AVAXUSDT",
    # "BCHUSDT",
    # "LINKUSDT",
    # "DOTUSDT",
    # "LTCUSDT",
    # "APTUSDT",
    # "UNIUSDT",
    # "ICPUSDT",
    # "ETCUSDT",
    # "POLUSDT",
    # "OMUSDT",
    # "ARBUSDT",
    # "FETUSDT",
    # "XMRUSDT",
    # "STXUSDT",
    # "FILUSDT",
    # "OPUSDT",
    # "ATOMUSDT",
    # "TIAUSDT",
    # "IMXUSDT",
    # "GRTUSDT",
    # "SEIUSDT",
]

COLAB = False
if COLAB:
    exchange_name = "kucoin"
else:
    exchange_name = "binance"

leverage = 1
start_date = "2020-01-01"
end_date = "2024-12-08"
strategy_type = ["long"]

if True:
    trix_lengths = create_range_list(5, 60, 5)
    trix_signal_lengths = create_range_list(5, 60, 5)
    trix_signal_types = ["ema", "sma"]
    long_ma_lengths = create_range_list(100, 1000, 100)
if False:
    trix_lengths = [5, 7, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47]
    trix_signal_lengths = [5, 7, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47]
    trix_signal_types = ["ema", "sma"]
    long_ma_lengths = [100, 200, 300, 400, 500, 600, 700]
elif False:
    trix_lengths = [7, 11, 15, 20, 30, 41, 45, 49]
    trix_signal_lengths = [7, 11, 15, 20, 30, 41, 45, 49]
    trix_signal_types = ["sma", "ema"]
    long_ma_lengths = [200, 300, 500, 700]
else:
    trix_lengths = [7, 49]
    trix_signal_lengths = [7]
    trix_signal_types = ["sma"]
    long_ma_lengths = [200]


# Define the possible values for each parameter
timeframes = ["1h", "2h", "4h"]
trading_pairs = lst_coin

size = [1]