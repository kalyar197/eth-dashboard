# data/__init__.py
# This file makes 'data' a Python package and allows importing the modules

# Import all data modules for easy access
from . import eth_price
from . import btc_price
from . import gold_price
from . import rsi
from . import bollinger_bands
from . import vwap  # Phase 4: Volume Weighted Average Price
from . import adx  # Phase 4: Average Directional Index
from . import time_transformer
from . import cache_manager

# List of all available data modules
__all__ = [
    'eth_price',
    'btc_price',
    'gold_price',
    'rsi',
    'bollinger_bands',
    'vwap',  # Phase 4
    'adx',   # Phase 4
    'time_transformer',
    'cache_manager'
]