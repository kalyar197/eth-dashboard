# config.py
"""
Centralized configuration file for all API keys and settings
"""

# API Keys
ALPHA_VANTAGE_API_KEY = '5EK27ZM3JQC594PO'  # Replace with your actual key

# Optional: Add other API keys if you want to switch between providers
CRYPTOCOMPARE_API_KEY = ''  # Optional - CryptoCompare works without key
COINGECKO_API_KEY = ''  # Optional - CoinGecko works without key

# Cache Settings
CACHE_DURATION = 300  # 5 minutes in seconds
RATE_LIMIT_DELAY = 2  # Seconds between API calls

# Data Settings
DEFAULT_DAYS = '365'
RSI_PERIOD = 14  # Period for RSI calculation

# API Provider Selection
# Options: 'alpha_vantage', 'cryptocompare', 'coingecko'
API_PROVIDER = 'alpha_vantage'