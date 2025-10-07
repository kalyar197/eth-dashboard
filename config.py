# config.py
"""
Centralized configuration file for all API keys and settings
"""

# API Keys
COINAPI_KEY = 'YOUR_COINAPI_KEY_HERE'  # For crypto data (BTC, ETH, dominance)
FMP_API_KEY = '74mkQbAh1DPHnRf1VoepvTTrLsvyvUf5'  # Financial Modeling Prep for Gold
FRED_API_KEY = 'f96bcbce8ee83ab7269b9a4b0859fcaf'  # Federal Reserve Economic Data for DXY

# Legacy/Deprecated API Keys (kept for reference only)
COINSTATS_API_KEY = 'hn8xFxvTblGTj6wEq35nxyijBlQNyBrdJUWqPIeHZCU='  # DEPRECATED
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
API_PROVIDER = 'mixed'  # Using multiple providers: CoinAPI for crypto, FMP for gold, FRED for DXY