# trends/backend/config.py
"""
Configuration for Google Trends data collection system.

This module defines:
- Geographic region codes (11 target regions)
- Fetch parameters (timeframe, rate limits)
- API settings
"""

# Number of days to fetch (180 = 6 months, 1095 = 3 years)
FETCH_DAYS = 180  # Start with 6 months, upgrade to 1095 for 3 years

# Rate limiting: Minimum seconds between Google Trends API requests
MIN_REQUEST_INTERVAL = 60  # 60 seconds recommended to avoid IP blocking

# Geographic region codes for Google Trends
# Format: {internal_key: {code, label, level, country}}
GEO_CODES = {
    'new_york': {
        'code': 'US-NY-501',
        'label': 'New York Metro',
        'level': 'DMA (Metro)',
        'country': 'United States'
    },
    'zurich': {
        'code': 'CH-ZH',
        'label': 'Zurich Canton',
        'level': 'Canton (State)',
        'country': 'Switzerland'
    },
    'dublin': {
        'code': 'IE',
        'label': 'Ireland',
        'level': 'Country',
        'country': 'Ireland',
        'note': 'City-level not available, using country code'
    },
    'london': {
        'code': 'GB-ENG',
        'label': 'England',
        'level': 'Region',
        'country': 'United Kingdom',
        'note': 'London CBD/Canary Wharf city-level not available, using England region'
    },
    'guadalajara': {
        'code': 'MX',
        'label': 'Mexico',
        'level': 'Country',
        'country': 'Mexico',
        'note': 'City-level not available, using country code'
    },
    'tokyo': {
        'code': 'JP-13',
        'label': 'Tokyo Prefecture',
        'level': 'Prefecture',
        'country': 'Japan'
    },
    'dubai': {
        'code': 'AE',
        'label': 'UAE',
        'level': 'Country',
        'country': 'United Arab Emirates',
        'note': 'City-level not available, using country code'
    },
    'nigeria': {
        'code': 'NG',
        'label': 'Nigeria',
        'level': 'Country',
        'country': 'Nigeria'
    },
    'mumbai': {
        'code': 'IN-MH',
        'label': 'Maharashtra State',
        'level': 'State',
        'country': 'India',
        'note': 'Mumbai city-level not available, using Maharashtra state'
    },
    'romania': {
        'code': 'RO',
        'label': 'Romania',
        'level': 'Country',
        'country': 'Romania'
    },
    'colombia': {
        'code': 'CO',
        'label': 'Colombia',
        'level': 'Country',
        'country': 'Colombia'
    },
    'beijing': {
        'code': 'CN-11',
        'label': 'Beijing Municipality',
        'level': 'Province/Municipality',
        'country': 'China'
    }
}

# List of all region codes for easy iteration
ALL_REGION_CODES = [region['code'] for region in GEO_CODES.values()]

# Metadata file paths
KEYWORDS_FILE = 'metadata/keywords.json'
FETCH_STATUS_FILE = 'metadata/fetch_status.json'

# Historical data directory
HISTORICAL_DATA_DIR = 'historical_data'

# Data format settings
TIMESTAMP_FORMAT = 'milliseconds'  # Unix timestamp in milliseconds
VALUE_RANGE = (0, 100)  # Google Trends normalization range

# Flask settings
FLASK_HOST = '127.0.0.1'
FLASK_PORT = 5001
CORS_ORIGINS = ['http://localhost:5173', 'http://127.0.0.1:5173']  # React dev server
