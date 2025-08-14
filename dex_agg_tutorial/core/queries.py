import os
import requests
import json
from retry import retry
from typing import Optional, Dict
from dotenv import load_dotenv

from web3 import Web3

from .validation import BadRequestException, Exchange
from .models import Pair

# Load environment variables from .env file
load_dotenv()

@retry(BadRequestException, delay=10, tries=2)
def request_json(url: str) -> dict:
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        raise BadRequestException(f"Status Code: {r.status_code} | {url}")


def query_uniswap_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Uniswap for token pair price."""
    try:
        # Get the Uniswap pool contract address
        pool_address = pair.pool_contracts.get("uniswap")
        if not pool_address:
            print(f"No Uniswap pool contract found for pair {pair.pair_id}")
            return None

        # Set up Web3 provider
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Load Uniswap pool ABI from config
        with open('uniswap_pool_abi.json', 'r') as abi_file:
            pool_abi = json.load(abi_file)
        
        pool_contract = web3.eth.contract(
            address=Web3.to_checksum_address(pool_address), 
            abi=pool_abi
        )

        # Get current price from slot0
        slot0 = pool_contract.functions.slot0().call()
        sqrt_price_x96 = slot0[0]

        # Convert sqrt_price (Q64.96 format) to actual price
        # sqrt_price is stored as u128 in Q64.96 fixed point format
        # To get actual price: (sqrt_price / 2^96)^2
        return float(((sqrt_price_x96) / 2 ** 96)**2)
        
    except Exception as e:
        print(f"Error querying Uniswap: {e}")
        return None


def query_hyperion_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Hyperion pool resource to get sqrt_price directly."""
    try:
        # Get the Hyperion pool contract address
        pool_address = pair.pool_contracts.get("hyperion")
        if not pool_address:
            print(f"No Hyperion pool contract found for pair {pair.pair_id}")
            return None
            
        # Query the LiquidityPoolV3 resource directly
        resource_url = f"{rpc_url}/v1/accounts/{pool_address}/resource/0x8b4a2c4bb53857c718a04c020b98f8c2e1f99a68b0f57389a8bf5434cd22e05c::pool_v3::LiquidityPoolV3"
        
        resource_data = request_json(resource_url)
        # Extract sqrt_price from the resource data (x64 fixed-point)
        sqrt_price = int(resource_data['data']['sqrt_price'])
        
        # Hyperion uses x64 fixed-point for sqrt_price, not Q64.96 like Uniswap
        # Formula: (sqrt_price / 2^64)^2
        actual_price = float((sqrt_price / (2**64))**2)
        
        return actual_price
            
    except Exception as e:
        print(f"Error querying Hyperion: {e}")
        return None


# Map price functions to their exchange ID
EXCHANGE_QUERY_FUNCTIONS = {
    Exchange.UNISWAP.id: query_uniswap_price,
    Exchange.HYPERION.id: query_hyperion_price,
}


def get_token_price(token_pair: str) -> Dict:
    """
    Get token prices from all active exchanges for a pair.
    Returns the best price and the separate exchange prices.
    """
    try:
        # Get the pair from database
        pair = Pair.objects.get(pair_id=token_pair)
    except Pair.DoesNotExist:
        return {"error": f"Pair {token_pair} not found"}
    
    prices = {}
    
    # We expect exchange to be defined for the pairs and supported as its admin defined
    for exchange_id in pair.active_exchanges:
        query_func = EXCHANGE_QUERY_FUNCTIONS[exchange_id]
        network = Exchange.get_network(exchange_id)
        rpc_url = os.getenv(f"{network.upper()}_RPC_URL")
        
        # Query the exchange
        price = query_func(pair, rpc_url)
        if price is not None:
            prices[exchange_id] = price
    
    # Return results
    if not prices:
        return {
            "token_pair": pair.pair_id,
            "error": "No prices available from any exchange"
        }
    
    return {
        "token_pair": pair.pair_id,
        "best_price": min(prices.values()), # Assumes pricing order is main/quote meaning lower is a better value (for buyers)
        "prices": prices
    }