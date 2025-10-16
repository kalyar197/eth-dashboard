# config.py
"""
Centralized configuration file for all API keys and settings
"""
import os

# Load environment variables from .env file
# IMPORTANT: You must install python-dotenv first: pip install python-dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()  # This loads variables from .env file into os.environ
    print("[OK] Environment variables loaded from .env file")
except ImportError:
    print("[WARNING] python-dotenv not installed. Run: pip install python-dotenv")
    print("[WARNING] Falling back to system environment variables only")

# API Keys (loaded from .env file or system environment)
COINAPI_KEY = os.environ.get('COINAPI_KEY')  # For crypto data (BTC, ETH, dominance)
FMP_API_KEY = os.environ.get('FMP_API_KEY')  # Financial Modeling Prep for Gold
FRED_API_KEY = os.environ.get('FRED_API_KEY')  # Federal Reserve Economic Data for DXY

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