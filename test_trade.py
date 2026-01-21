#!/usr/bin/env python3
"""
Test script: Buy 1 share of AAPL, wait 10 seconds, then sell it.
For IBKR paper trading account.
"""

import os
import time

from dotenv import load_dotenv
from ib_insync import IB, Stock, MarketOrder

load_dotenv()

def main():
    ib = IB()

    # Connection settings
    host = os.getenv('TWS_HOST', '127.0.0.1')
    port = int(os.getenv('TWS_PORT', '7497'))
    client_id = 2  # Use different client_id from main bot

    print(f"Connecting to TWS at {host}:{port}...")
    ib.connect(host, port, clientId=client_id)
    print("Connected!")

    # Create AAPL contract
    contract = Stock('AAPL', 'SMART', 'USD')
    ib.qualifyContracts(contract)
    print(f"Contract: {contract}")

    # Buy 1 share
    print("\n--- BUYING 1 share of AAPL ---")
    buy_order = MarketOrder('BUY', 1)
    buy_trade = ib.placeOrder(contract, buy_order)

    # Wait for fill
    while not buy_trade.isDone():
        ib.sleep(1)

    if buy_trade.orderStatus.status == 'Filled':
        print(f"BUY filled @ ${buy_trade.orderStatus.avgFillPrice:.2f}")
    else:
        print(f"BUY order status: {buy_trade.orderStatus.status}")
        ib.disconnect()
        return

    # Wait 10 seconds
    print("\nWaiting 10 seconds...")
    for i in range(10, 0, -1):
        print(f"  {i}...")
        ib.sleep(1)

    # Sell 1 share
    print("\n--- SELLING 1 share of AAPL ---")
    sell_order = MarketOrder('SELL', 1)
    sell_trade = ib.placeOrder(contract, sell_order)

    # Wait for fill
    while not sell_trade.isDone():
        ib.sleep(1)

    if sell_trade.orderStatus.status == 'Filled':
        print(f"SELL filled @ ${sell_trade.orderStatus.avgFillPrice:.2f}")
    else:
        print(f"SELL order status: {sell_trade.orderStatus.status}")

    # Calculate P&L
    buy_price = buy_trade.orderStatus.avgFillPrice
    sell_price = sell_trade.orderStatus.avgFillPrice
    pnl = sell_price - buy_price
    print(f"\n--- RESULT ---")
    print(f"Bought @ ${buy_price:.2f}")
    print(f"Sold   @ ${sell_price:.2f}")
    print(f"P&L: ${pnl:.2f}")

    ib.disconnect()
    print("\nDisconnected. Done!")

if __name__ == '__main__':
    main()
