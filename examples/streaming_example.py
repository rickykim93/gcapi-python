"""Stream live prices for a few markets.

Run with credentials in the environment (install the package first: pip install -e .)::

    GCAPI_USERNAME=... GCAPI_PASSWORD=... GCAPI_APPKEY=... python examples/streaming_example.py
"""

import os
import time

from gcapi import GCapiClient

MARKET_NAMES = ["USD/JPY", "USD/CAD"]


def main():
    # Optional: use the keyring package for secure password storage instead of env vars
    client = GCapiClient(
        username=os.environ["GCAPI_USERNAME"],
        password=os.environ["GCAPI_PASSWORD"],
        appkey=os.environ["GCAPI_APPKEY"],
    )

    # Set the Trading Account ID on the client
    client.get_account_info()

    # Get Market IDs for Streaming
    market_ids = [client.get_market_info(market_name=name, get="MarketId") for name in MARKET_NAMES]

    # Initialize Streaming Client
    stream = client.init_streaming_client()
    stream.subscribe_to_streaming(market_id_list=market_ids)

    try:
        while True:
            print(stream.real_time_snapshot())
            time.sleep(1)
    except KeyboardInterrupt:
        stream.unsubscribe_to_streaming()


if __name__ == "__main__":
    main()
