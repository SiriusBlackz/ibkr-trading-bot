#!/usr/bin/env python3
"""Simple script to test TWS connection."""

from ib_insync import IB


def main():
    ib = IB()

    print("Connecting to TWS on port 7497...")
    try:
        ib.connect('127.0.0.1', 7497, clientId=1)
        print("Connected successfully!\n")

        # Get account info
        accounts = ib.managedAccounts()
        print(f"Managed accounts: {accounts}")

        # Get account summary
        print("\nAccount Summary:")
        for account in accounts:
            summary = ib.accountSummary(account)
            for item in summary:
                if item.tag in ['NetLiquidation', 'TotalCashValue', 'BuyingPower', 'AvailableFunds']:
                    print(f"  {item.tag}: {item.value} {item.currency}")

        print("\nDisconnecting...")
        ib.disconnect()
        print("Done.")

    except Exception as e:
        print(f"Connection failed: {e}")
        print("\nMake sure TWS is running and configured to accept API connections on port 7497")


if __name__ == '__main__':
    main()
