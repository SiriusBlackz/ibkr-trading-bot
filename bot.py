#!/usr/bin/env python3
"""
Interactive Brokers Trading Bot
MA Crossover Strategy using ib_insync
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from ib_insync import IB, Stock, MarketOrder, util

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trades.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TradingBot:
    def __init__(self, config_path: str = 'config.json'):
        self.config = self._load_config(config_path)
        self.ib = IB()
        self.contract: Optional[Stock] = None
        self.running = False
        self.position = 0
        self.avg_cost = 0.0

        # Connection settings from environment
        self.host = os.getenv('TWS_HOST', '127.0.0.1')
        self.port = int(os.getenv('TWS_PORT', '7497'))
        self.client_id = int(os.getenv('CLIENT_ID', '1'))

        # Setup signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config: {config}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info("Shutdown signal received, closing connections...")
        self.running = False

    def connect(self) -> bool:
        """Connect to TWS/IB Gateway."""
        try:
            logger.info(f"Connecting to TWS at {self.host}:{self.port} (client_id={self.client_id})")
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            logger.info("Connected to TWS successfully")

            # Create contract for the configured ticker
            self.contract = Stock(
                self.config['ticker'],
                self.config['exchange'],
                self.config['currency']
            )

            # Qualify the contract to get full details
            self.ib.qualifyContracts(self.contract)
            logger.info(f"Trading contract: {self.contract}")

            return True
        except Exception as e:
            logger.error(f"Failed to connect to TWS: {e}")
            return False

    def disconnect(self):
        """Disconnect from TWS."""
        if self.ib.isConnected():
            self.ib.disconnect()
            logger.info("Disconnected from TWS")

    def get_historical_data(self, days: int = 100) -> list:
        """Fetch historical daily bars for MA calculation."""
        try:
            bars = self.ib.reqHistoricalData(
                self.contract,
                endDateTime='',
                durationStr=f'{days} D',
                barSizeSetting='1 day',
                whatToShow='TRADES',
                useRTH=True,
                formatDate=1
            )
            return bars
        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            return []

    def calculate_ma(self, bars: list, period: int) -> Optional[float]:
        """Calculate simple moving average for given period."""
        if len(bars) < period:
            logger.warning(f"Not enough data for {period}-day MA (have {len(bars)} bars)")
            return None

        closes = [bar.close for bar in bars[-period:]]
        return sum(closes) / period

    def get_signal(self) -> Optional[str]:
        """Determine trading signal based on MA crossover."""
        bars = self.get_historical_data()
        if not bars:
            return None

        fast_period = self.config['ma_fast_period']
        slow_period = self.config['ma_slow_period']

        ma_fast = self.calculate_ma(bars, fast_period)
        ma_slow = self.calculate_ma(bars, slow_period)

        if ma_fast is None or ma_slow is None:
            return None

        current_price = bars[-1].close
        logger.info(f"Price: ${current_price:.2f} | MA{fast_period}: ${ma_fast:.2f} | MA{slow_period}: ${ma_slow:.2f}")

        # Check for crossover
        if ma_fast > ma_slow:
            return 'BUY'
        elif ma_fast < ma_slow:
            return 'SELL'

        return 'HOLD'

    def get_position(self) -> tuple:
        """Get current position for the contract."""
        positions = self.ib.positions()
        for pos in positions:
            if pos.contract.symbol == self.config['ticker']:
                self.position = int(pos.position)
                self.avg_cost = pos.avgCost
                return self.position, self.avg_cost

        self.position = 0
        self.avg_cost = 0.0
        return 0, 0.0

    def get_pnl(self) -> Optional[float]:
        """Calculate unrealized P&L for current position."""
        if self.position == 0:
            return 0.0

        # Get current market price
        ticker = self.ib.reqMktData(self.contract, '', False, False)
        self.ib.sleep(2)  # Wait for data

        if ticker.last and ticker.last > 0:
            current_price = ticker.last
        elif ticker.close and ticker.close > 0:
            current_price = ticker.close
        else:
            logger.warning("Could not get current market price for P&L calculation")
            return None

        self.ib.cancelMktData(self.contract)

        unrealized_pnl = (current_price - self.avg_cost) * self.position
        return unrealized_pnl

    def place_order(self, action: str, quantity: int) -> bool:
        """Place a market order."""
        try:
            order = MarketOrder(action, quantity)
            trade = self.ib.placeOrder(self.contract, order)

            logger.info(f"Order placed: {action} {quantity} {self.config['ticker']}")

            # Wait for order to fill (with timeout)
            timeout = 30
            start = time.time()
            while not trade.isDone() and (time.time() - start) < timeout:
                self.ib.sleep(1)

            if trade.orderStatus.status == 'Filled':
                fill_price = trade.orderStatus.avgFillPrice
                logger.info(f"Order filled: {action} {quantity} @ ${fill_price:.2f}")
                return True
            else:
                logger.warning(f"Order status: {trade.orderStatus.status}")
                return False

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return False

    def is_market_hours(self) -> bool:
        """Check if within US market hours (simplified check)."""
        now = datetime.now()
        # Monday = 0, Friday = 4
        if now.weekday() > 4:
            return False

        # Market hours: 9:30 AM - 4:00 PM ET (simplified, assumes local time is ET)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)

        return market_open <= now <= market_close

    def execute_strategy(self):
        """Execute one iteration of the trading strategy."""
        # Get current position
        position, avg_cost = self.get_position()
        logger.info(f"Current position: {position} shares @ ${avg_cost:.2f}")

        # Get trading signal
        signal = self.get_signal()
        if signal is None:
            logger.warning("Could not determine trading signal")
            return

        logger.info(f"Signal: {signal}")

        max_position = self.config['position_size']

        # Execute based on signal
        if signal == 'BUY' and position <= 0:
            # Buy signal and no long position
            quantity = max_position
            if position < 0:
                # Close short position first
                quantity = abs(position) + max_position
            logger.info(f"BUY signal - placing order for {quantity} shares")
            self.place_order('BUY', quantity)

        elif signal == 'SELL' and position > 0:
            # Sell signal and have long position - close it
            logger.info(f"SELL signal - closing position of {position} shares")
            self.place_order('SELL', position)

        else:
            logger.info(f"No action needed (signal={signal}, position={position})")

        # Show P&L
        pnl = self.get_pnl()
        if pnl is not None:
            logger.info(f"Unrealized P&L: ${pnl:.2f}")

    def run(self):
        """Main bot loop."""
        if not self.connect():
            logger.error("Failed to connect, exiting")
            return

        self.running = True
        check_interval = self.config['check_interval_seconds']

        logger.info(f"Bot started - checking every {check_interval} seconds")
        logger.info(f"Strategy: MA{self.config['ma_fast_period']}/MA{self.config['ma_slow_period']} crossover on {self.config['ticker']}")
        logger.info("Press Ctrl+C to stop")

        try:
            while self.running:
                if self.is_market_hours():
                    logger.info("-" * 50)
                    self.execute_strategy()
                else:
                    logger.info("Outside market hours, waiting...")

                # Sleep in small increments to allow for clean shutdown
                for _ in range(check_interval):
                    if not self.running:
                        break
                    self.ib.sleep(1)

        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            self.disconnect()
            logger.info("Bot stopped")


def main():
    """Entry point."""
    logger.info("=" * 50)
    logger.info("Interactive Brokers Trading Bot")
    logger.info("=" * 50)

    bot = TradingBot()
    bot.run()


if __name__ == '__main__':
    main()
