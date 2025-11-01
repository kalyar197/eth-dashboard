# data/spx_oscillator.py
"""
S&P 500 (SPX) Oscillator Plugin

Wraps spx_price module to provide SPX closing prices as an oscillator.
This allows SPX to be normalized against crypto/gold prices for divergence analysis.

Returns simple data structure: [[timestamp, close_price], ...]

Trading significance:
- SPX represents traditional US equity markets
- Divergence between SPX and crypto/gold signals risk rotation between asset classes
- Strong SPX vs weak crypto: Flight to traditional equities (risk-off in crypto)
- Weak SPX vs strong crypto: Risk-on in digital assets, equity weakness
- SPX vs Gold divergence: Classic risk-on (stocks up, gold down) vs risk-off (stocks down, gold up)
- Useful for understanding macro risk sentiment and capital flows between markets
"""

from . import spx_price


def get_metadata():
    """Returns metadata describing how this data should be displayed"""
    return {
        'label': 'SPX (S&P 500)',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'SPX Index',
        'unit': '',
        'chartType': 'line',
        'color': '#0052CC',  # Blue color for SPX
        'strokeWidth': 2,
        'description': 'S&P 500 index - traditional equity vs crypto/gold divergence',
        'data_structure': 'simple',
        'components': ['timestamp', 'spx_close_price']
    }


def get_data(days='365'):
    """
    Fetches SPX price data and extracts closing prices.

    Args:
        days (str): Number of days to return ('7', '30', '180', '1095', 'max')

    Returns:
        dict: {
            'metadata': metadata dict,
            'data': [[timestamp, close_price], ...],
            'structure': 'simple'
        }
    """
    metadata = get_metadata()

    try:
        # Fetch SPX OHLCV data from spx_price module
        spx_result = spx_price.get_data(days)
        spx_ohlcv = spx_result['data']

        if not spx_ohlcv:
            raise ValueError("No SPX price data available")

        # Extract closing prices from OHLCV structure
        # OHLCV format: [timestamp, open, high, low, close, volume]
        # We want: [timestamp, close]
        simple_data = []
        for item in spx_ohlcv:
            if len(item) >= 5:  # Ensure OHLCV structure
                timestamp = item[0]
                close_price = item[4]  # Close is at index 4
                simple_data.append([timestamp, close_price])

        if not simple_data:
            raise ValueError("No valid SPX closing prices extracted")

        print(f"[SPX Oscillator] Returning {len(simple_data)} SPX price points")
        if simple_data:
            print(f"[SPX Oscillator] SPX range: {simple_data[0][1]:.2f} to {simple_data[-1][1]:.2f}")

        return {
            'metadata': metadata,
            'data': simple_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[SPX Oscillator] Error in get_data: {e}")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }
