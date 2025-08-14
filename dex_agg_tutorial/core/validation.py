from enum import Enum


class Network(Enum):
    """Supported blockchain networks."""
    ETHEREUM = "mainnet"
    APTOS = "aptosMainnet" # follow wagmi/viem style chain naming where possible


class Exchange(Enum):
    """Supported DEX exchanges with their network information."""
    
    # Format: (exchange_id, network)
    UNISWAP = ("uniswap", Network.ETHEREUM)
    HYPERION = ("hyperion", Network.APTOS)
    
    def __init__(self, exchange_id, network):
        self.id = exchange_id
        self.network = network

    # to make sure Django can check the model field we define the choices.
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(exchange.id, exchange.name.title()) for exchange in cls]
    
    # Additionally we can use this function in a public view or internal function later to validate an exchange
    @classmethod
    def values(cls):
        """Return list of all exchange values."""
        return [exchange.id for exchange in cls]
    
    @classmethod
    def get_network(cls, exchange_id):
        """Get the network string for a given exchange ID (mainnet, aptosMainnet etc.)"""
        exchange_map = {exchange.id: exchange.network.value for exchange in cls}
        return exchange_map.get(exchange_id)


class TokenPairFormatExcepetion(Exception):
    """
    Raised when a token_pair string doesnt match it's expected format
    """

    pass


class BadRequestException(Exception):
    """
    Raised when an on-chain query does not respond with a 200 status
    """

    pass
