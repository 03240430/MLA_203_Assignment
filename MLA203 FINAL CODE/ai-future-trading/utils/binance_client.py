import os
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY", "")
API_SECRET = os.getenv("BINANCE_API_SECRET", "")
TESTNET = os.getenv("BINANCE_TESTNET", "True").lower() in ("1","true","yes")

def create_client():
    if not API_KEY or not API_SECRET:
        print("Warning: Missing API keys. Public endpoints only.")
        client = Client()
    else:
        client = Client(API_KEY, API_SECRET)

    TESTNET = os.getenv("BINANCE_TESTNET", "True").lower() in ("1","true","yes")

    if TESTNET:
        client.API_URL = "https://testnet.binancefuture.com/fapi"
        print("Using Binance Futures TESTNET")

    return client
