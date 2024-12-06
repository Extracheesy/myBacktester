lst_coin = [
    "BTC/USDT", #
    "ETH/USDT",
    "SOL/USDT", #
    "BNB/USDT",
    "XRP/USDT",
    "DOGE/USDT",
    # "ADA/USDT",
    "TRX/USDT",
    # "AVAX/USDT",
    "SHIB/USDT",
    "TON/USDT",
    "SUI/USDT",
    # "BCH/USDT",
    # "LINK/USDT",
    # "DOT/USDT",
    "PEPE/USDT",
    "XLM/USDT",
    "NEAR/USDT",
    # "LTC/USDT",
    # "APT/USDT",
    # "UNI/USDT",
    "HBAR/USDT",
    # "ICP/USDT",
    # "ETC/USDT",
    "BONK/USDT",
    "KAS/USDT",
    "TAO/USDT",
    "RENDER/USDT",
    # "POL/USDT",
    # "OM/USDT",
    "WIF/USDT",
    # "ARB/USDT",
    # "FET/USDT",
    # "XMR/USDT",
    # "STX/USDT",
    # "FIL/USDT",
    # "OP/USDT",
    "VET/USDT",
    "AAVE/USDT",
    # "ATOM/USDT",
    "FLOKI/USDT",
    "INJ/USDT",
    # "TIA/USDT",
    # "IMX/USDT",
    # "GRT/USDT",
    # "SEI/USDT",
]

COLAB = True
if COLAB:
    exchange_name = "kucoin"
else:
    exchange_name = "binance"

leverage = 1
start_date = "2020-01-01"
end_date = None
strategy_type = ["long"]


trix_lengths = [5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47]
trix_signal_lengths = [5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47]
trix_signal_types = ["ema", "sma"]
long_ma_lengths = [100, 200, 300, 400, 500, 600, 700]

"""
trix_lengths = [7, 11, 15, 20, 30, 41, 45, 49]
trix_signal_lengths = [7, 11, 15, 20, 30, 41, 45, 49]
trix_signal_types = ["sma", "ema"]
long_ma_lengths = [200, 300, 500, 700]
"""
"""
trix_lengths = [7, 49]
trix_signal_lengths = [7]
trix_signal_types = ["sma"]
long_ma_lengths = [200]
"""
# Define the possible values for each parameter
timeframes = ["1h", "2h", "4h"]
trading_pairs = lst_coin

size = [1]