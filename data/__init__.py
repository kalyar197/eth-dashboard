# data/__init__.py
# This file makes 'data' a Python package and allows importing the modules

# Import core infrastructure modules
from . import time_transformer
from . import cache_manager
from . import incremental_data_manager

# Import data plugins
from . import eth_price
from . import btc_price
from . import gold_price
from . import spx_price

# Import price oscillator plugins (for Breakdown tab)
from . import eth_price_alpaca
from . import gold_price_oscillator
from . import spx_price_fmp

# Import oscillator plugins
from . import rsi
from . import macd_histogram
from . import adx
from . import atr

# Import overlay plugins
from . import sma
from . import parabolic_sar

# List of all available data modules
__all__ = [
    'time_transformer',
    'cache_manager',
    'incremental_data_manager',
    'eth_price',
    'btc_price',
    'gold_price',
    'spx_price',
    'eth_price_alpaca',
    'gold_price_oscillator',
    'spx_price_fmp',
    'rsi',
    'macd_histogram',
    'adx',
    'atr',
    'sma',
    'parabolic_sar'
]