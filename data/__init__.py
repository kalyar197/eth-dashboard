# data/__init__.py
# This file makes 'data' a Python package and allows importing the modules

# Import all data modules for easy access
from . import eth_price
from . import gold_price
from . import rsi
from . import btc_dominance
from . import eth_dominance
from . import usdt_dominance
from . import bollinger_bands
from . import dxy
from . import obv  # Phase 3: On-Balance Volume indicator
from . import atr  # Phase 3: Average True Range indicator
from . import vwap  # Phase 4: Volume Weighted Average Price
from . import macd  # Phase 4: MACD indicator
from . import adx  # Phase 4: Average Directional Index
from . import google_trends  # Google Trends search interest data
from . import time_transformer
from . import cache_manager

# List of all available data modules
__all__ = [
    'eth_price',
    'gold_price',
    'rsi',
    'btc_dominance',
    'eth_dominance',
    'usdt_dominance',
    'bollinger_bands',
    'dxy',
    'obv',   # Phase 3
    'atr',   # Phase 3
    'vwap',  # Phase 4
    'macd',  # Phase 4
    'adx',   # Phase 4
    'google_trends',
    'time_transformer',
    'cache_manager'
]