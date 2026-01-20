# Interactive Brokers Trading Bot

A Python trading bot that uses a Moving Average crossover strategy with Interactive Brokers via the `ib_insync` library.

## Strategy

The bot implements a simple MA crossover strategy:
- **BUY signal**: When the fast MA (20-day) crosses above the slow MA (50-day)
- **SELL signal**: When the fast MA crosses below the slow MA
- Position size: 100 shares (configurable)

## Prerequisites

1. **Interactive Brokers Account** - Paper trading or live account
2. **TWS (Trader Workstation)** or **IB Gateway** installed and running
3. **Python 3.8+**

## TWS Configuration

Before running the bot, configure TWS to accept API connections:

1. Open TWS and log in to your **paper trading** account
2. Go to **Edit → Global Configuration → API → Settings**
3. Enable **"Enable ActiveX and Socket Clients"**
4. Set **Socket port** to `7497` (paper trading default)
5. Disable **"Read-Only API"** to allow order placement
6. Add `127.0.0.1` to **"Trusted IPs"** (or uncheck "Allow connections from localhost only")
7. Click **Apply** and restart TWS

## Installation

1. Clone the repository and navigate to the directory:
   ```bash
   cd ibkr-trading-bot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the environment template and configure:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` if you need to change connection settings:
   ```
   TWS_HOST=127.0.0.1
   TWS_PORT=7497
   CLIENT_ID=1
   ```

## Configuration

Edit `config.json` to customize the trading parameters:

```json
{
    "ticker": "AAPL",
    "exchange": "SMART",
    "currency": "USD",
    "ma_fast_period": 20,
    "ma_slow_period": 50,
    "position_size": 100,
    "check_interval_seconds": 60
}
```

| Parameter | Description |
|-----------|-------------|
| `ticker` | Stock symbol to trade |
| `exchange` | Exchange (SMART for best routing) |
| `currency` | Currency for the contract |
| `ma_fast_period` | Fast moving average period (days) |
| `ma_slow_period` | Slow moving average period (days) |
| `position_size` | Maximum shares per position |
| `check_interval_seconds` | How often to check for signals |

## Usage

1. Ensure TWS is running and logged into paper trading
2. Run the bot:
   ```bash
   python bot.py
   ```

3. The bot will:
   - Connect to TWS on port 7497
   - Fetch historical data for the configured ticker
   - Calculate moving averages and determine signals
   - Place orders when crossover conditions are met
   - Log all activity to `trades.log` and console
   - Check every 60 seconds during market hours

4. Stop the bot with `Ctrl+C` for a clean shutdown

## Logging

All activity is logged to:
- **Console** - Real-time monitoring
- **trades.log** - Persistent log file

Log entries include:
- Connection status
- Price and MA values
- Trading signals
- Order placements and fills
- Position and P&L updates

## Port Reference

| Port | Environment |
|------|-------------|
| 7496 | TWS Live Trading |
| 7497 | TWS Paper Trading |
| 4001 | IB Gateway Live |
| 4002 | IB Gateway Paper |

## Disclaimer

This bot is for **educational purposes only**. Trading involves substantial risk of loss. Always test thoroughly with paper trading before considering live trading. The authors are not responsible for any financial losses incurred.

## License

MIT License
