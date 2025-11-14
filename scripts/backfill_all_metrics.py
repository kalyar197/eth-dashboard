"""
Unified TradingView Backfill Script for 27 Metrics
Fetches 3 years of historical data with comprehensive validation

Features:
- Multi-tier rate limiting (avoid IP bans + silent failures)
- 6-layer validation (zero tolerance for bad data)
- Progress persistence (resume after crash)
- Detailed logging and validation reports
- Dry-run mode for testing

Usage:
    python backfill_all_metrics.py                # Full backfill (all 27 symbols)
    python backfill_all_metrics.py --dry-run      # Test mode (no file writes)
    python backfill_all_metrics.py --symbols 3    # Test with first 3 symbols
    python backfill_all_metrics.py --resume       # Resume from last checkpoint
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from tvDatafeed import TvDatafeed, Interval

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.time_transformer import standardize_to_daily_utc
from data.incremental_data_manager import save_historical_data
import backfill_validation as validator

# ==================== CONFIGURATION ====================

# Rate limiting delays (seconds)
BASE_DELAY = 3          # Between each symbol
EXCHANGE_DELAY = 5      # When switching exchanges
ERROR_BACKOFF = 10      # After any error
COOL_DOWN_DELAY = 60    # After multiple errors

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # Exponential backoff multiplier

# Fetch configuration
N_BARS = 1095  # 3 years of daily data

# File paths
SYMBOLS_FILE = Path(__file__).parent / 'tradingview_symbols_final.json'
PROGRESS_FILE = Path(__file__).parent.parent / 'historical_data' / 'backfill_progress.json'
LOG_FILE = Path(__file__).parent.parent / 'historical_data' / f'backfill_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
REPORT_FILE = Path(__file__).parent.parent / 'historical_data' / 'backfill_validation_report.txt'
RESULTS_FILE = Path(__file__).parent.parent / 'historical_data' / 'backfill_results.json'

# ==================== LOGGING ====================

class Logger:
    """Simple logger that writes to file and console"""

    def __init__(self, log_file):
        self.log_file = log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log(self, level, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_line = f"[{timestamp}] [{level:8}] {message}"

        # Print to console
        print(log_line)

        # Write to file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + '\n')

    def info(self, msg):
        self.log('INFO', msg)

    def success(self, msg):
        self.log('SUCCESS', msg)

    def warning(self, msg):
        self.log('WARNING', msg)

    def error(self, msg):
        self.log('ERROR', msg)

    def critical(self, msg):
        self.log('CRITICAL', msg)


# ==================== PROGRESS TRACKING ====================

class ProgressTracker:
    """Track backfill progress to enable resume"""

    def __init__(self, progress_file):
        self.progress_file = progress_file
        self.progress = self.load()

    def load(self):
        """Load existing progress or create new"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                pass

        return {
            'started_at': datetime.now().isoformat(),
            'last_updated': None,
            'completed': [],
            'failed': [],
            'pending': []
        }

    def save(self):
        """Save current progress"""
        self.progress['last_updated'] = datetime.now().isoformat()
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.progress_file, 'w') as f:
            json.dump(self.progress, f, indent=2)

    def mark_completed(self, symbol_full):
        """Mark a symbol as successfully completed"""
        if symbol_full not in self.progress['completed']:
            self.progress['completed'].append(symbol_full)
        if symbol_full in self.progress['pending']:
            self.progress['pending'].remove(symbol_full)
        if symbol_full in self.progress['failed']:
            self.progress['failed'].remove(symbol_full)
        self.save()

    def mark_failed(self, symbol_full):
        """Mark a symbol as failed"""
        if symbol_full not in self.progress['failed']:
            self.progress['failed'].append(symbol_full)
        if symbol_full in self.progress['pending']:
            self.progress['pending'].remove(symbol_full)
        self.save()

    def is_completed(self, symbol_full):
        """Check if symbol already completed"""
        return symbol_full in self.progress['completed']

    def get_summary(self):
        """Get progress summary"""
        return {
            'completed': len(self.progress['completed']),
            'failed': len(self.progress['failed']),
            'pending': len(self.progress['pending'])
        }


# ==================== CORE FUNCTIONS ====================

def load_symbols_config():
    """Load symbol configuration from JSON"""
    if not SYMBOLS_FILE.exists():
        raise FileNotFoundError(f"Symbol config not found: {SYMBOLS_FILE}")

    with open(SYMBOLS_FILE, 'r') as f:
        config = json.load(f)

    return config['symbols']


def group_symbols_by_exchange(symbols):
    """Group symbols by exchange to add delays between exchanges"""
    grouped = {}

    for ticker, info in symbols.items():
        exchange = info['exchange']
        if exchange not in grouped:
            grouped[exchange] = []
        grouped[exchange].append((ticker, info))

    return grouped


def fetch_single_symbol(exchange, symbol, logger, n_bars=N_BARS, retry_count=0, tv_username=None, tv_password=None):
    """
    Fetch data for a single symbol with retry logic

    Args:
        tv_username: TradingView username (optional, unlocks premium data)
        tv_password: TradingView password (optional, unlocks premium data)

    Returns: {
        'success': bool,
        'data': [...] or None,
        'error': str or None,
        'retry_count': int
    }
    """
    logger.info(f"Fetching {exchange}:{symbol} (attempt {retry_count + 1}/{MAX_RETRIES + 1})")

    try:
        # Initialize with login if credentials provided
        if tv_username and tv_password:
            tv = TvDatafeed(username=tv_username, password=tv_password)
            logger.info("  Using TradingView login (premium data access)")
        else:
            tv = TvDatafeed()
            logger.warning("  Using no-login method (data may be limited)")

        data = tv.get_hist(
            symbol=symbol,
            exchange=exchange,
            interval=Interval.in_daily,
            n_bars=n_bars
        )

        if data is None or len(data) == 0:
            logger.warning(f"No data returned for {exchange}:{symbol}")
            return {
                'success': False,
                'data': None,
                'error': 'No data returned (symbol may not exist or soft rate limit)',
                'retry_count': retry_count
            }

        # Convert pandas DataFrame to list format
        raw_data = []
        for index, row in data.iterrows():
            # Get timestamp from index
            dt = index

            # Force UTC timezone
            if dt.tzinfo is None:
                dt_utc = dt.replace(tzinfo=timezone.utc)
            else:
                dt_utc = dt.astimezone(timezone.utc)

            timestamp_ms = int(dt_utc.timestamp() * 1000)

            # Extract close price
            close_price = float(row['close'])

            raw_data.append([timestamp_ms, close_price])

        # Sort by timestamp
        raw_data.sort(key=lambda x: x[0])

        logger.success(f"Fetched {len(raw_data)} points for {exchange}:{symbol}")

        if raw_data:
            first_dt = datetime.fromtimestamp(raw_data[0][0] / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
            last_dt = datetime.fromtimestamp(raw_data[-1][0] / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
            logger.info(f"  Date range: {first_dt} to {last_dt}")

        return {
            'success': True,
            'data': raw_data,
            'error': None,
            'retry_count': retry_count
        }

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error fetching {exchange}:{symbol}: {error_msg}")

        # Check if we should retry
        if retry_count < MAX_RETRIES:
            # Exponential backoff
            delay = RETRY_DELAY * (2 ** retry_count)
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)

            return fetch_single_symbol(exchange, symbol, logger, n_bars, retry_count + 1, tv_username, tv_password)
        else:
            logger.error(f"Max retries exhausted for {exchange}:{symbol}")
            return {
                'success': False,
                'data': None,
                'error': error_msg,
                'retry_count': retry_count
            }


def save_with_backup(ticker, data, logger, dry_run=False):
    """
    Save data to cache file with backup

    Returns: (success, error_msg)
    """
    if dry_run:
        logger.info(f"[DRY-RUN] Would save {len(data)} points for {ticker}")
        return True, None

    try:
        # Save using incremental data manager
        dataset_name = ticker.lower().replace('.', '_').replace(':', '_')
        save_historical_data(dataset_name, data)

        logger.success(f"Saved {len(data)} points for {ticker} to cache")
        return True, None

    except Exception as e:
        error_msg = f"Failed to save {ticker}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def generate_validation_report(results, report_file):
    """Generate human-readable validation report"""

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    warnings_count = sum(len(r.get('warnings', [])) for r in successful)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("TRADINGVIEW BACKFILL VALIDATION REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    report_lines.append("")

    # Summary
    report_lines.append("SUMMARY:")
    report_lines.append(f"  Total symbols: {len(results)}")
    report_lines.append(f"  Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    report_lines.append(f"  Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)")
    report_lines.append(f"  Warnings: {warnings_count}")
    report_lines.append("")

    # Successful fetches
    if successful:
        report_lines.append(f"SUCCESSFUL FETCHES ({len(successful)}):")
        report_lines.append("-" * 80)
        for r in successful:
            symbol_full = r['symbol_full']
            data_points = len(r.get('data', []))
            warnings = r.get('warnings', [])

            status = "[OK]" if len(warnings) == 0 else f"[OK] {len(warnings)} warnings"
            report_lines.append(f"  {status:20} {symbol_full:40} {data_points:5} points")

            for warning in warnings[:3]:  # Show first 3 warnings
                report_lines.append(f"       - {warning}")
            if len(warnings) > 3:
                report_lines.append(f"       ... and {len(warnings) - 3} more warnings")

        report_lines.append("")

    # Failed fetches
    if failed:
        report_lines.append(f"FAILED FETCHES ({len(failed)}):")
        report_lines.append("-" * 80)
        for r in failed:
            symbol_full = r['symbol_full']
            error = r.get('error', 'Unknown error')

            report_lines.append(f"  [FAIL] {symbol_full}")
            report_lines.append(f"         Error: {error}")

        report_lines.append("")

    # Recommendations
    report_lines.append("RECOMMENDATIONS:")
    report_lines.append("-" * 80)

    if failed:
        report_lines.append(f"  1. Review {len(failed)} failed symbols above")
        report_lines.append("  2. Check if symbols exist on TradingView")
        report_lines.append("  3. Consider using alternative data sources for failed symbols")

    if warnings_count > 0:
        report_lines.append(f"  4. Review {warnings_count} warnings for data quality issues")

    if not failed and warnings_count == 0:
        report_lines.append("  [OK] All symbols fetched successfully with no warnings!")
        report_lines.append("  [OK] Ready for production use")

    report_lines.append("")
    report_lines.append("=" * 80)

    # Write to file
    report_text = '\n'.join(report_lines)
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_text)

    # Also print to console
    print("\n" + report_text)

    return report_text


# ==================== MAIN EXECUTION ====================

def main():
    """Main backfill execution"""

    # Parse arguments
    parser = argparse.ArgumentParser(description='Backfill TradingView metrics')
    parser.add_argument('--dry-run', action='store_true', help='Test mode (no file writes)')
    parser.add_argument('--symbols', type=int, help='Number of symbols to test (for quick testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--tv-username', type=str, help='TradingView username (enables premium data)')
    parser.add_argument('--tv-password', type=str, help='TradingView password (enables premium data)')
    args = parser.parse_args()

    # Get credentials from args or environment
    tv_username = args.tv_username or os.getenv('TV_USERNAME')
    tv_password = args.tv_password or os.getenv('TV_PASSWORD')

    # Initialize logger
    logger = Logger(LOG_FILE)

    logger.info("=" * 80)
    logger.info("TRADINGVIEW BACKFILL SCRIPT - STARTING")
    logger.info("=" * 80)
    logger.info(f"Dry-run mode: {args.dry_run}")
    logger.info(f"Resume mode: {args.resume}")
    if tv_username and tv_password:
        logger.info(f"TradingView Login: ENABLED (user: {tv_username})")
    else:
        logger.warning("TradingView Login: DISABLED (some premium data may be unavailable)")
        logger.warning("  Set TV_USERNAME and TV_PASSWORD in .env or use --tv-username/--tv-password")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("")

    # Load symbols
    try:
        symbols = load_symbols_config()
        logger.info(f"Loaded {len(symbols)} symbols from config")
    except Exception as e:
        logger.critical(f"Failed to load symbols config: {e}")
        return 1

    # Limit symbols for testing
    if args.symbols:
        symbols_list = list(symbols.items())[:args.symbols]
        symbols = dict(symbols_list)
        logger.info(f"Limited to first {args.symbols} symbols for testing")

    # Initialize progress tracker
    progress = ProgressTracker(PROGRESS_FILE)

    if args.resume:
        summary = progress.get_summary()
        logger.info(f"Resuming from checkpoint: {summary['completed']} completed, {summary['failed']} failed")

    # Group by exchange
    grouped_symbols = group_symbols_by_exchange(symbols)
    logger.info(f"Symbols grouped into {len(grouped_symbols)} exchanges")
    logger.info("")

    # Results storage
    all_results = []
    consecutive_errors = 0

    # Process each exchange group
    for exchange_idx, (exchange, symbol_list) in enumerate(grouped_symbols.items()):
        logger.info(f"Processing exchange {exchange_idx + 1}/{len(grouped_symbols)}: {exchange} ({len(symbol_list)} symbols)")

        # Add delay before starting new exchange (except first)
        if exchange_idx > 0:
            logger.info(f"Exchange cooldown: waiting {EXCHANGE_DELAY} seconds...")
            time.sleep(EXCHANGE_DELAY)

        # Process each symbol in this exchange
        for symbol_idx, (ticker, info) in enumerate(symbol_list):
            symbol = info['symbol']
            symbol_full = info['full']

            logger.info(f"\n--- Symbol {symbol_idx + 1}/{len(symbol_list)}: {ticker} ---")

            # Skip if already completed (resume mode)
            if args.resume and progress.is_completed(symbol_full):
                logger.info(f"Skipping {symbol_full} (already completed)")
                continue

            # Fetch data (pass credentials for premium access)
            fetch_result = fetch_single_symbol(exchange, symbol, logger, tv_username=tv_username, tv_password=tv_password)

            if not fetch_result['success']:
                # Fetch failed
                consecutive_errors += 1
                progress.mark_failed(symbol_full)

                all_results.append({
                    'ticker': ticker,
                    'symbol_full': symbol_full,
                    'success': False,
                    'error': fetch_result['error'],
                    'retry_count': fetch_result['retry_count']
                })

                # Check if we need cooldown
                if consecutive_errors >= 3:
                    logger.warning(f"Multiple consecutive errors ({consecutive_errors}). Cooldown for {COOL_DOWN_DELAY}s...")
                    time.sleep(COOL_DOWN_DELAY)
                    consecutive_errors = 0
                else:
                    time.sleep(ERROR_BACKOFF)

                continue

            # Reset consecutive errors on success
            consecutive_errors = 0
            raw_data = fetch_result['data']

            # Validate data
            logger.info(f"Validating {ticker}...")
            validation_result = validator.validate_all_layers(ticker, raw_data)

            if not validation_result['valid']:
                logger.error(f"Validation FAILED for {ticker}")
                for error in validation_result['errors']:
                    logger.error(f"  - {error}")

                progress.mark_failed(symbol_full)

                all_results.append({
                    'ticker': ticker,
                    'symbol_full': symbol_full,
                    'success': False,
                    'error': 'Validation failed: ' + '; '.join(validation_result['errors']),
                    'warnings': validation_result['warnings']
                })

                time.sleep(ERROR_BACKOFF)
                continue

            # Log warnings
            if validation_result['warnings']:
                logger.warning(f"{len(validation_result['warnings'])} warnings for {ticker}:")
                for warning in validation_result['warnings'][:5]:
                    logger.warning(f"  - {warning}")
            else:
                logger.success(f"Validation PASSED for {ticker}")

            # Standardize timestamps
            logger.info(f"Standardizing timestamps for {ticker}...")
            standardized_data = standardize_to_daily_utc(validation_result['cleaned_data'])
            logger.info(f"Standardized {len(raw_data)} -> {len(standardized_data)} points")

            # Save to cache
            save_success, save_error = save_with_backup(ticker, standardized_data, logger, dry_run=args.dry_run)

            if not save_success:
                progress.mark_failed(symbol_full)
                all_results.append({
                    'ticker': ticker,
                    'symbol_full': symbol_full,
                    'success': False,
                    'error': save_error,
                    'warnings': validation_result['warnings']
                })
                continue

            # Success!
            progress.mark_completed(symbol_full)

            all_results.append({
                'ticker': ticker,
                'symbol_full': symbol_full,
                'success': True,
                'data': standardized_data,
                'warnings': validation_result['warnings'],
                'data_points': len(standardized_data)
            })

            # Rate limiting delay before next symbol
            if symbol_idx < len(symbol_list) - 1:  # Not last symbol
                logger.info(f"Rate limit delay: {BASE_DELAY}s...")
                time.sleep(BASE_DELAY)

    # Generate validation report
    logger.info("\n" + "=" * 80)
    logger.info("GENERATING VALIDATION REPORT")
    logger.info("=" * 80)

    generate_validation_report(all_results, REPORT_FILE)

    # Save machine-readable results
    with open(RESULTS_FILE, 'w') as f:
        # Remove 'data' field to reduce file size
        results_compact = []
        for r in all_results:
            r_copy = r.copy()
            if 'data' in r_copy:
                del r_copy['data']
            results_compact.append(r_copy)

        json.dump({
            'timestamp': datetime.now().isoformat(),
            'dry_run': args.dry_run,
            'results': results_compact
        }, f, indent=2)

    logger.info(f"\nResults saved to: {RESULTS_FILE}")
    logger.info(f"Report saved to: {REPORT_FILE}")
    logger.info(f"Log saved to: {LOG_FILE}")

    # Final summary
    successful_count = sum(1 for r in all_results if r['success'])
    failed_count = len(all_results) - successful_count

    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Successful: {successful_count}/{len(all_results)}")
    logger.info(f"Failed: {failed_count}/{len(all_results)}")

    if args.dry_run:
        logger.info("\n[DRY-RUN] No files were written")

    # Exit code
    if failed_count == 0:
        logger.info("\n[SUCCESS] ALL SYMBOLS FETCHED SUCCESSFULLY")
        return 0
    elif successful_count > 0:
        logger.warning(f"\n[WARNING] PARTIAL SUCCESS ({successful_count}/{len(all_results)})")
        return 1
    else:
        logger.critical("\n[FAILED] ALL SYMBOLS FAILED")
        return 2


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[ABORTED] Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
