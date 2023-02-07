# Optional Keyring for Secure Password Storage
# import keyring
import sys, pathlib
main_directory = str(pathlib.Path(__file__).parent.parent)
sys.path.insert(1, main_directory)
from gcapi.gcapi_client import GCapiClient

# Trading Credentials 
username = 'test'
password = 'test_password'
apikey = '12345'

# Initalize Trading Client
GC_Client = GCapiClient(username=username, password=password, appkey=apikey)

# Set the Trading Account ID in GC_Client
a = GC_Client.get_account_info()

# Get Market IDs for Streaming
market_names = ['USD/JPY','USD/CAD']
market_ids = []
for market in market_names:
    market_id = GC_Client.get_market_info(market_name=market)['Markets'][0]['MarketId']
    market_ids.append(market_id)

# Initalize Streaming Client
GC_Stream = GC_Client.init_streaming_client()
GC_Client.subscribe_to_streaming(market_id_list=market_ids)

while True:
    real_time_data = GC_Stream.real_time_snapshot()
    print(real_time_data)