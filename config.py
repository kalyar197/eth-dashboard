# config.py
"""
Centralized configuration file for all API keys and settings
"""

# API Keys
COINAPI_KEY = 'YOUR_COINAPI_KEY_HERE'  # Add your CoinAPI key here
FMP_API_KEY = '74mkQbAh1DPHnRf1VoepvTTrLsvyvUf5'  # DEPRECATED - will be removed
COINSTATS_API_KEY = 'hn8xFxvTblGTj6wEq35nxyijBlQNyBrdJUWqPIeHZCU='  # DEPRECATED - will be removed

# Legacy API Keys (kept for reference only)
ALPHA_VANTAGE_API_KEY = '5EK27ZM3JQC594PO'  # Legacy - not used
CRYPTOCOMPARE_API_KEY = ''  # Optional - not used
COINGECKO_API_KEY = ''  # Optional - not used

# Cache Settings
CACHE_DURATION = 300  # 5 minutes in seconds
RATE_LIMIT_DELAY = 2  # Seconds between API calls

# Data Settings
DEFAULT_DAYS = '365'
RSI_PERIOD = 14  # Period for RSI calculation

# API Provider Selection
API_PROVIDER = 'coinapi'  # Changed from 'fmp' to 'coinapi'