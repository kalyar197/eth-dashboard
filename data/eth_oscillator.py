# data/eth_oscillator.py
"""
ETH Price Oscillator Plugin

Wraps eth_price module to provide ETH closing prices as an oscillator.
This allows ETH to be normalized against BTC price for divergence analysis.

Returns simple data structure: [[timestamp, close_price], ...]

Trading significance:
- ETH is the second-largest cryptocurrency and often leads or lags BTC
- Divergence between ETH and BTC can signal relative strength/weakness
- Strong ETH vs weak BTC: Alt season, risk-on in crypto
- Weak ETH vs strong BTC: Flight to BTC safety, risk-off in crypto
- Useful for BTC traders to understand crypto market internal dynamics
"""

from . import eth_price


def get_metadata():
    """Returns metadata describing how this data should be displayed"""
    return {
        'label': 'ETH Price',
        'oscillator': True,
        'yAxisId': 'oscillator',
        'yAxisLabel': 'ETH Price (USD)',
        'unit': '$',
        'chartType': 'line',
        'color': '#627EEA',  # Ethereum color
        'strokeWidth': 2,
        'description': 'ETH spot price - crypto alternative vs BTC divergence',
        'data_structure': 'simple',
        'components': ['timestamp', 'eth_close_price']
    }


def get_data(days='365'):
    """
    Fetches ETH price data and extracts closing prices.

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
        # Fetch ETH OHLCV data from eth_price module
        eth_result = eth_price.get_data(days)
        eth_ohlcv = eth_result['data']

        if not eth_ohlcv:
            raise ValueError("No ETH price data available")

        # Extract closing prices from OHLCV structure
        # OHLCV format: [timestamp, open, high, low, close, volume]
        # We want: [timestamp, close]
        simple_data = []
        for item in eth_ohlcv:
            if len(item) >= 5:  # Ensure OHLCV structure
                timestamp = item[0]
                close_price = item[4]  # Close is at index 4
                simple_data.append([timestamp, close_price])

        if not simple_data:
            raise ValueError("No valid ETH closing prices extracted")

        print(f"[ETH Oscillator] Returning {len(simple_data)} ETH price points")
        if simple_data:
            print(f"[ETH Oscillator] ETH price range: ${simple_data[0][1]:.2f} to ${simple_data[-1][1]:.2f}")

        return {
            'metadata': metadata,
            'data': simple_data,
            'structure': 'simple'
        }

    except Exception as e:
        print(f"[ETH Oscillator] Error in get_data: {e}")
        return {
            'metadata': metadata,
            'data': [],
            'structure': 'simple'
        }
