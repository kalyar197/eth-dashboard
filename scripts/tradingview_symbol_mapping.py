"""
TradingView Symbol Mapping for 28 New Metrics

Format: EXCHANGE:SYMBOL
Common exchanges:
- GLASSNODE: On-chain metrics provider
- COINMETRICS: Blockchain data provider
- DEFILLAMA: TVL data provider
- CRYPTOCAP: Market cap data
- NASDAQ/NYSE: Stock tickers
"""

SYMBOL_MAPPING = {
    # ==================== ON-CHAIN METRICS (Glassnode/Coin Metrics) ====================

    # Bitcoin SOPR (Spent Output Profit Ratio)
    'BTC_SOPR': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_SOPR',
        'full': 'GLASSNODE:BTC_SOPR',
        'description': 'Bitcoin Spent Output Profit Ratio',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0.5,
        'max_val': 2.0
    },

    # Bitcoin Median Volume
    'BTC_MEDIANVOLUME': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_MEDIANVOLUME',
        'full': 'GLASSNODE:BTC_MEDIANVOLUME',
        'description': 'Bitcoin Median Transaction Volume',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None  # No upper limit
    },

    # Bitcoin Mean Transaction Fees
    'BTC_MEANTXFEES': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_MEANTXFEES',
        'full': 'GLASSNODE:BTC_MEANTXFEES',
        'description': 'Bitcoin Mean Transaction Fees (USD)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Sending Addresses
    'BTC_SENDINGADDRESSES': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_SENDINGADDRESSES',
        'full': 'GLASSNODE:BTC_SENDINGADDRESSES',
        'description': 'Bitcoin Sending Addresses (Active)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Active Supply 1 Year
    'BTC_ACTIVE1Y': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_ACTIVE1Y',
        'full': 'GLASSNODE:BTC_ACTIVE1Y',
        'description': 'Bitcoin Active Supply (1 Year)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': 21_000_000
    },

    # Bitcoin Receiving Addresses
    'BTC_RECEIVINGADDRESSES': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_RECEIVINGADDRESSES',
        'full': 'GLASSNODE:BTC_RECEIVINGADDRESSES',
        'description': 'Bitcoin Receiving Addresses (Active)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin New Addresses
    'BTC_NEWADDRESSES': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_NEWADDRESSES',
        'full': 'GLASSNODE:BTC_NEWADDRESSES',
        'description': 'Bitcoin New Addresses',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin SER (Spent Entities Ratio)
    'BTC_SER': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_SER',
        'full': 'GLASSNODE:BTC_SER',
        'description': 'Bitcoin Spent Entities Ratio',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Average Transaction Size
    'BTC_AVGTX': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_AVGTX',
        'full': 'GLASSNODE:BTC_AVGTX',
        'description': 'Bitcoin Average Transaction Size (USD)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Transaction Count
    'BTC_TXCOUNT': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_TXCOUNT',
        'full': 'GLASSNODE:BTC_TXCOUNT',
        'description': 'Bitcoin Transaction Count (Daily)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Supply in Addresses with Balance
    'BTC_SPLYADRBAL': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_SPLYADRBAL',
        'full': 'GLASSNODE:BTC_SPLYADRBAL',
        'description': 'Bitcoin Supply in Addresses with Balance',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': 21_000_000
    },

    # Bitcoin Addresses with Supply 1 in 10k
    'BTC_ADDRESSESSUPPLY1IN10K': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_ADDRESSESSUPPLY1IN10K',
        'full': 'GLASSNODE:BTC_ADDRESSESSUPPLY1IN10K',
        'description': 'Bitcoin Addresses Holding 1/10,000 of Supply',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Large Transaction Count
    'BTC_LARGETXCOUNT': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_LARGETXCOUNT',
        'full': 'GLASSNODE:BTC_LARGETXCOUNT',
        'description': 'Bitcoin Large Transaction Count (>$100k)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Active Supply 1 Year (alternative)
    'BTC_ACTIVESUPPLY1Y': {
        'exchange': 'GLASSNODE',
        'symbol': 'BTC_ACTIVESUPPLY1Y',
        'full': 'GLASSNODE:BTC_ACTIVESUPPLY1Y',
        'description': 'Bitcoin Active Supply (Last 1 Year)',
        'provider': 'Glassnode',
        'category': 'on_chain',
        'min_val': 0,
        'max_val': 21_000_000
    },

    # ==================== SOCIAL METRICS (Santiment/LunarCrush) ====================

    # Bitcoin Posts Created
    'BTC_POSTSCREATED': {
        'exchange': 'SANTIMENT',  # Or LUNARCRUSH
        'symbol': 'BTC_POSTSCREATED',
        'full': 'SANTIMENT:BTC_POSTSCREATED',
        'description': 'Bitcoin Social Posts Created',
        'provider': 'Santiment',
        'category': 'social',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Contributors Created
    'BTC_CONTRIBUTORSCREATED': {
        'exchange': 'SANTIMENT',
        'symbol': 'BTC_CONTRIBUTORSCREATED',
        'full': 'SANTIMENT:BTC_CONTRIBUTORSCREATED',
        'description': 'Bitcoin New Contributors',
        'provider': 'Santiment',
        'category': 'social',
        'min_val': 0,
        'max_val': None
    },

    # Bitcoin Social Dominance
    'BTC_SOCIALDOMINANCE': {
        'exchange': 'SANTIMENT',
        'symbol': 'BTC_SOCIALDOMINANCE',
        'full': 'SANTIMENT:BTC_SOCIALDOMINANCE',
        'description': 'Bitcoin Social Dominance %',
        'provider': 'Santiment',
        'category': 'social',
        'min_val': 0,
        'max_val': 100
    },

    # Bitcoin Active Contributors
    'BTC_CONTRIBUTORSACTIVE': {
        'exchange': 'SANTIMENT',
        'symbol': 'BTC_CONTRIBUTORSACTIVE',
        'full': 'SANTIMENT:BTC_CONTRIBUTORSACTIVE',
        'description': 'Bitcoin Active Contributors',
        'provider': 'Santiment',
        'category': 'social',
        'min_val': 0,
        'max_val': None
    },

    # ==================== DEFI/TVL METRICS ====================

    # Bitcoin Staking TVL
    'BTCST_TVL': {
        'exchange': 'DEFILLAMA',
        'symbol': 'BTCST_TVL',
        'full': 'DEFILLAMA:BTCST_TVL',
        'description': 'Bitcoin Staking Total Value Locked',
        'provider': 'DefiLlama',
        'category': 'defi',
        'min_val': 0,
        'max_val': None
    },

    # ==================== MARKET METRICS ====================

    # iShares Bitcoin Trust ETF
    'IBIT': {
        'exchange': 'NASDAQ',
        'symbol': 'IBIT',
        'full': 'NASDAQ:IBIT',
        'description': 'iShares Bitcoin Trust ETF',
        'provider': 'NASDAQ',
        'category': 'etf',
        'min_val': 0,
        'max_val': None
    },

    # Grayscale Bitcoin Mini Trust (ticker changed to BTC in July 2024)
    'GGBTC': {
        'exchange': 'NYSE',
        'symbol': 'BTC',  # NOTE: Ticker is BTC, not GGBTC!
        'full': 'NYSE:BTC',
        'description': 'Grayscale Bitcoin Mini Trust',
        'provider': 'NYSE',
        'category': 'etf',
        'min_val': 0,
        'max_val': None
    },

    # Total Altcoin Market Cap (excluding BTC & ETH)
    'TOTAL3': {
        'exchange': 'CRYPTOCAP',
        'symbol': 'TOTAL3',
        'full': 'CRYPTOCAP:TOTAL3',
        'description': 'Total Altcoin Market Cap (excl BTC/ETH)',
        'provider': 'CryptoCap',
        'category': 'market',
        'min_val': 0,
        'max_val': None
    },

    # Fed Reverse Repo Operations
    'RRPONTSYD': {
        'exchange': 'FRED',  # Federal Reserve Economic Data
        'symbol': 'RRPONTSYD',
        'full': 'FRED:RRPONTSYD',
        'description': 'Federal Reserve Reverse Repo Outstanding',
        'provider': 'FRED',
        'category': 'macro',
        'min_val': 0,
        'max_val': None
    },

    # ==================== STABLECOIN METRICS ====================

    # Stablecoin Dominance
    'STABLE.C.D': {
        'exchange': 'CRYPTOCAP',
        'symbol': 'STABLE.C.D',
        'full': 'CRYPTOCAP:STABLE.C.D',
        'description': 'Stablecoin Dominance %',
        'provider': 'CryptoCap',
        'category': 'stablecoin',
        'min_val': 0,
        'max_val': 100
    },

    # USDT Premium/Discount
    'USDTUSD.PM': {
        'exchange': 'COINMETRICS',
        'symbol': 'USDTUSD',  # Simplified from USDTUSD.PM
        'full': 'COINMETRICS:USDTUSD',
        'description': 'USDT Premium/Discount to USD',
        'provider': 'Coin Metrics',
        'category': 'stablecoin',
        'min_val': 0.95,
        'max_val': 1.05
    },

    # USDT Transfer Speed
    'USDT_TFSPS': {
        'exchange': 'GLASSNODE',
        'symbol': 'USDT_TFSPS',
        'full': 'GLASSNODE:USDT_TFSPS',
        'description': 'USDT Transfer Speed (Transactions per Second)',
        'provider': 'Glassnode',
        'category': 'stablecoin',
        'min_val': 0,
        'max_val': None
    },

    # USDT Average Transaction Size
    'USDT_AVGTX': {
        'exchange': 'GLASSNODE',
        'symbol': 'USDT_AVGTX',
        'full': 'GLASSNODE:USDT_AVGTX',
        'description': 'USDT Average Transaction Size',
        'provider': 'Glassnode',
        'category': 'stablecoin',
        'min_val': 0,
        'max_val': None
    },
}

# Symbols that need verification (uncertain about exact TradingView format)
NEEDS_VERIFICATION = [
    'BTC_SER',  # Might be COINMETRICS instead of GLASSNODE
    'BTCST_TVL',  # DefiLlama integration on TradingView uncertain
    'RRPONTSYD',  # FRED data might not be on TradingView
    'USDTUSD.PM',  # Unusual notation, might be different format
    'USDT_TFSPS',  # Transfer speed metric unusual
    'BTC_POSTSCREATED',  # Santiment might use different exchange code
    'BTC_CONTRIBUTORSCREATED',
    'BTC_CONTRIBUTORSACTIVE',
]

def get_symbol_info(ticker):
    """Get full symbol information for a ticker"""
    return SYMBOL_MAPPING.get(ticker, None)

def get_full_symbol(ticker):
    """Get full TradingView symbol (EXCHANGE:SYMBOL)"""
    info = SYMBOL_MAPPING.get(ticker)
    return info['full'] if info else None

def print_all_mappings():
    """Print all symbol mappings organized by category"""
    categories = {}
    for ticker, info in SYMBOL_MAPPING.items():
        cat = info['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((ticker, info))

    print("="*80)
    print("TRADINGVIEW SYMBOL MAPPING - 28 METRICS")
    print("="*80)

    for category, items in sorted(categories.items()):
        print(f"\n{category.upper()} ({len(items)} metrics):")
        print("-" * 80)
        for ticker, info in items:
            verify_flag = " [NEEDS VERIFICATION]" if ticker in NEEDS_VERIFICATION else ""
            print(f"  {ticker:30} -> {info['full']:35} {verify_flag}")
            print(f"  {'':30}    {info['description']}")

    print(f"\n{'='*80}")
    print(f"TOTAL: {len(SYMBOL_MAPPING)} symbols")
    print(f"NEEDS VERIFICATION: {len(NEEDS_VERIFICATION)} symbols")
    print(f"{'='*80}\n")

if __name__ == '__main__':
    print_all_mappings()

    print("\nSYMBOLS REQUIRING MANUAL VERIFICATION:")
    print("-" * 80)
    for ticker in NEEDS_VERIFICATION:
        info = SYMBOL_MAPPING[ticker]
        print(f"\n{ticker}:")
        print(f"  Proposed: {info['full']}")
        print(f"  Reason: Uncertain about exact TradingView format/availability")
        print(f"  Action: Test with tvDatafeed.get_hist()")
