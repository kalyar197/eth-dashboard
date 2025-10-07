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
from . import obv  # NEW: On-Balance Volume indicator
from . import atr  # NEW: Average True Range indicator
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
    'obv',  # NEW
    'atr',  # NEW
    'time_transformer',
    'cache_manager'
]