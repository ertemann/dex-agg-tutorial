
from enum import Enum

class Exchange(Enum):
    """Supported DEX exchanges."""
    UNISWAP = 'uniswap'
    HYPERION = 'hyperion'
    
    # to make sure Django can check the model field we define the choices.
    @classmethod
    def choices(cls):
        """Return choices for Django model field."""
        return [(exchange.value, exchange.name.title()) for exchange in cls]
    
    # Additionally we can use this function in a public view or internal function later to validate an exchange
    @classmethod
    def values(cls):
        """Return list of all exchange values."""
        return [exchange.value for exchange in cls]



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
