# data/gold_oscillator.py
"""
Gold Price Oscillator Plugin

Wraps gold_price module to provide gold closing prices as an oscillator.
This allows gold to be normalized against crypto prices (BTC/ETH) for divergence analysis.

Returns simple data structure: [[timestamp, close_price], ...]

Trading significance:
- Gold and crypto often compete as alternative assets to fiat
- Divergence between gold and crypto can signal risk sentiment shifts
- Strong gold vs weak crypto: Flight to traditional safe haven
- Strong crypto vs weak gold: Risk-on, digital asset preference
"""

from . import gold_price


def get_metadata():
    """Returns metadata describing how this data should be displayed"""
    return {
        'label': 'Gold Price',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'Gold Price (USD/oz)',
        'unit': '$',
        'chartType': 'line',
        'color': '#FFD700',  # Gold color
        'strokeWidth': 2,
        'description': 'Gold spot price - safe haven vs crypto divergence',
        'data_structure': 'simple',
        'components': ['timestamp', 'gold_close_price']
    }


def get_data(days='365'):
    """
    Fetches gold price data and extracts closing prices.

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
        # Fetch gold OHLCV data from gold_price module
        gold_result = gold_price.get_data(days)
        gold_ohlcv = gold_result['data']

        if not gold_ohlcv:
            raise ValueError("No gold price data available")

        # Extract closing prices from OHLCV structure
        # OHLCV format: [timestamp, open, high, low, close, volume]
        # We want: [timestamp, close]
        simple_data = []
        for item in gold_ohlcv:
            if len(item) >= 5:  # Ensure OHLCV structure
                timestamp = item[0]
                close_price = item[4]  # Close is at index 4
                simple_data.append([timestamp, close_price])

        if not simple_data:
            raise ValueError("No valid gold closing prices extracted")

        print(f"[Gold Oscillator] Returning {len(simple_data)} gold price points")
        if simple_data:
            print(f"[Gold Oscillator] Gold price range: ${simple_data[0][1]:.2f} to ${simple_data[-1][1]:.2f}")

        return {
            'metadata': metadata,
            'data': simple_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[Gold Oscillator] Error in get_data: {e}")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }
