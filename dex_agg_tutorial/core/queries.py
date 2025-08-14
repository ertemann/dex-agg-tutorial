import os
import requests
from retry import retry
from typing import Optional, Dict

from .validation import BadRequestException, Exchange
from .models import Pair

#uniswap
# import IUniswapV3PoolABI from '@uniswap/v3-core/artifacts/contracts/interfaces/IUniswapV3Pool.sol/IUniswapV3Pool.json'
# import { ethers } from 'ethers'


@retry(BadRequestException, delay=10, tries=2)
def request_json(url: str) -> dict:
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        raise BadRequestException(f"Status Code: {r.status_code} | {url}")


def query_uniswap_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Uniswap for token pair price."""
    # Implement Uniswap-specific price query logic
    try:
        return 1e6
    except Exception as e:
        print(f"Error querying Uniswap: {e}")
        return None


def query_hyperion_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Hyperion for token pair price."""
    # Implement Hyperion-specific price query
    try:
        return 1e6
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
    
    # We don't have to check if all these items are available as we expect the Admin to only add exchanges and token pairs that match
    # We should however double check if the pairs itself are stull supported which is done in the price function itself.
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
        "best_price": min(prices.values()),
        "prices": prices
    }