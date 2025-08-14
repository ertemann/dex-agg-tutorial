Welcome to this small tutorial on building a crypto dex aggregator in Python

# pre-requisites/Setup

## python setup

Install Poetry `pipx install poetry`

Create poetry project `poetry new PROJECT_NAME`

add Ruff, blackl mypy `poetry add black ruff mypy`

You can use ruff and black using: `poetry run black dex_agg_tutorial` and `poetry run ruff check` and `poetry run mypy`

setup as git 

1. `git init`
2. `git checkout -b master`
3. `git add .`
4. `git commit -a -m "project setup"`
5. Create a new EMPTY repo on your git account
6. `git remote add origin https://github.com/USERNAME/REPO_NAME.git`
7. `git push --set-upstream origin master`

You can also use the above tools to setup a CI in github to format, lint and typecheck our files using our current Poetry environment or as we do in this tutorial, setup a pre-push hook that is called when you make git commands in this environment.

You can find the hook in the home directory of this codebase under `pre-push.sh` and copy it to your github folder using `cp pre-push.sh .git/hooks/pre-push`. Just make it executable and you will always have a pretty codebase `.git/hooks/pre-push`.

You can configure what exactly black and ruff will touch in the pyproject.toml. A good example for a configuration can be found [here](https://github.com/astral-sh/ruff).

## Implementation plan and requirements

Requirements:
- Build a basic dex-aggregator API
- Query prices of token pairs from 2 DEXs
- Handle correct input validation
- Add readme to run the API locally

We can query the prices from the chain using libraries like Viem/Wagmi or straight up Python Request. For the Web API we can use the popular Django REST framework so we are future proofing if we need to add complex cache, user UIs/swagger or backends to the equation. We can handle the validation of input with some common pattern-matching and potentially a whitelisted set of token-pairs. For the Readme it is likely best to build a simple docker container so running the system locally won't be an issue.

## Setting up django

add django REST `poetry add django djangorestframework`

If you want to learn more about django it is best to take a look at the [following tutorial](https://docs.djangoproject.com/en/5.2/intro/tutorial01/) as we will be skipping over some of the basics of building an API with django. In short you should view it as a complete web-framework that uses python to host server-side functions (aka a backend) to serve, receive and store data.

To get started with django we can run: ` poetry run django-admin startproject config dex_agg_tutorial` to create the files we need to manage the API and associated models. Most importantly this creates the settings.py and urls.py files in our new config directory so we can configure the API urls that will load upon launching the app.

You can now test the Django setup using: `poetry run python dex_agg_tutorial manage.py runserver` and we should add the django restframework implementation into these settings following [this setup instruction](https://www.django-rest-framework.org/#quickstart).

1. add rest_framework to INSTALLED_APPS in settings.py
2. add an initial URL to the urlpatterns list in urls.py
3. add global access settings for the api to settings.py

``` python
# allow anyone to view the api urls/endpoints
REST_FRAMEWORK = {"DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"]}
```

For this tutorial we will only consider an admin user (which is standard protected under /admin) and a public view, but you can extend the access model of the API to different tiers of paid users without too much problem. You can setup different endpoints by combining "view" classes from django with the proper url setup. For extended documentation on creating and managing views in the django restframework you can navigate [here](https://www.django-rest-framework.org/api-guide/views/).

Lastly in our setup we will make a directory for our core logic to separate it from the django setup `mkdir dex_agg_tutorial/core` (and `touch dex_agg_tutorial/core/__init__.py` and `cp /tests /dex/_agg_tutorial/core/tests` and `rm tests`) after which our general setup is complete and our directory structure should look like this:

```
  dex-agg-tutorial/
  ├── dex_agg_tutorial/
  │   ├── __init__.py
  │   ├── config/
  │   │   ├── __init__.py
  │   │   ├── asgi.py
  │   │   ├── settings.py
  │   │   ├── urls.py
  │   │   └── wsgi.py
  │   ├── core/
  │   │   ├── __init__.py
  │   └── manage.py
  ├── docs/
  │   ├── ANALYSIS.md
  │   └── TUTORIAL.md
  ├── tests/
  │   └── __init__.py
  ├── poetry.lock
  ├── pyproject.toml
  └── README.md
  ```

add the Core django app to installed apps to truly complete our django setup
  
```python
INSTALLED_APPS = [
....
    "core",
]
```

# The core application

As discussed before our app consists of the following items: the django api and config, the django model, the logic to query the right token price and a validation setup of input and output. To simplify our coding going forward we are therefore splitting up our logic into three files and will create a set of example functions to determine our app logic. For the tutorial we are naming the files `views.py`, `models.py`,`validation.py` and `queries.py` which are hosted under the `/core` directory.

## building the skeleton

In API/web development its often best to start with the skeleton of your final product rather than the functions that will deliver the data for it. Hence why we focus first on the creation of the Django model and views that will make up the webapp and endpoints for the user.

First, the final product, a request/GET api to get the best price between 2 DEXs. Lets create the view in django as follows:

in views.py
```python
    def get(self, request, token_pair: str):
        try:
            pair = Pair.objects.get(pair_id=token_pair.upper())
            if not pair.active_exchanges:
                return Response(
                    {"error": f"Token pair {token_pair} is not active on any exchange"},
                    status=400,
                )
        except Pair.DoesNotExist:
            return Response(
                {"error": f"Token pair {token_pair} is not supported"}, status=404
            )

        price_data = get_token_price(token_pair)

        if "error" in price_data:
            return Response(price_data, status=503)  # Service Unavailable

        return Response(price_data, status=200)
```

This GET function will:

1. Validate that a price can be provided for the requested pair by checking our integrations or respond with an EndpointNotSupported status code
2. Request price data from the chain in a function we can build later
3. Respond with valid data or an error because the function did not work properly

We can wrap the above GET function in a django view and configure our URL to access it to create the first complete endpoint.

in views.py
```Python
class PriceView(APIView):
    """
    View to access the best price from 2 exchanges for supported tokenpairs.

    * no authentication
    """

..... ### Add above function
```

and in config.urls.py
```python
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.DefaultView.as_view(), name="default"),
    path("price/<str:token_pair>/", views.PriceView.as_view(), name="price"),
]
```

As you saw from the above `get` function we are referencing some pieces that we haven't created yet. Most obvious is the price function but more important for now is the input validation and management through our `Pair` Django model. This is a small database item that hosts all the pairs a user will be able to query for alongside with key information about the exchange and tokens in question. In Crypto there are many different standards by which people build applications and connection to those apps but a few things are relatively constant. 

-------- This section explains something about the basics of a DEX/AMM and can be skipped if you are familiar with this concept
A decentralized exchange (sometimes called AMM for automated marketmaker) is an application consisting of mainly 2 things, Pools and a router. Pools are vaults of money in often 2 (but can be more) tokens whereby the distribution of those funds in the vault (either the quantity for v2/XYK amms [INFO](https://medium.com/codex/an-introduction-to-automated-market-making-994bc76c61f4), or the orders set for v3/CL style DEX [INFO]) determine the price for which they can be traded against each other. Pools are created by something called a factory contract for any specific pair of tokens people want to trade and this mechanism is often permissionless meaning anyone can create new pools and therefore new tokens to trade on the dex. The router is the system the application uses to give user the best price over all pools in a single interface so often allows people to get a hypothetical quote for their token and swap size they can decide to execute if favourable. All of these components are single contracts and defined by their unique contract address, which for pools can often be found determinstically. Additionally tokens and pools handle data in specific formats to improve the contract efficiency in compute and storage and to work around the non-float limitation in blockchain. Tokens therefore have something called a Decimal value which is the multiplaction factor for the float--> int conversion, this is different for every token. Most nomenclature for DEXs and tokens come from the Ethereum application Uniswap, if you want to learn more I would highly recommend to check out their [V3 docs](https://docs.uniswap.org/sdk/v3/overview) and scroll through their contracts and API references on [Etherscan](https://etherscan.io/address/0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640#readContract).
--------

So the information we will need to query prices on basically all DEXs are: `Tokenin`, `TokenOut`, the pool `contractAddress` and the `Decimals` of both tokens. You can often query some information for each combination if you have atleast the contract address of the pool but for this example we will create an admin handled backend that hosts the full information for each pair and pool the DEX aggregator wants to support. This creates a consistent input vs output expectation for the user and allows us to have a "supported_pairs" endpoint.

Let us create this model and APIView.

```python
from django.db import models

class Pair(models.Model):
    """Model representing a token pair."""

    uid = models.IntegerField(unique=True)
    pair_id = models.CharField(max_length=40, unique=True)
    pool_contracts = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapping of exchange IDs to their pool contract addresses",
    )
    base_token = models.CharField(max_length=20)
    quote_token = models.CharField(max_length=20)
    base_token_decimals = models.IntegerField(default=18)
    quote_token_decimals = models.IntegerField(default=18)
    active_exchanges = models.JSONField(
        default=list,
        blank=True,
        help_text="List of exchange IDs where this pair is active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

Please recognise that all models in Django are properly typed and checked through their own interface giving us a solid level of safety. We can extend on this overtime by for example checking the exact architecture of the strings like needing a specific format, starting with a specific character and so fort. For now some basic validation checks can be implemented using the proper field types and a max length. You could also use the PostgresSql database instead of the standard defined sqLite to limit fields like the `pool_contracts` and `active_exchanges` to very specific fields. Find docs for that [here](https://docs.djangoproject.com/en/5.2/ref/models/constraints/).

We can now define a get and post method to see and add pairs/pools to the above model/database. We will make the Post method admin-only so we can ensure we are only supporting pairs and exchanges that we have actually created price querying functionality for.

```python
class PairsView(APIView):

    def get(self, request, format=None):
        # Get pairs that have at least one active exchange
        pairs = Pair.objects.exclude(active_exchanges=[]).values()
        return Response(pairs, status=200)

    def post(self, request, format=None):
        # Check admin permission for POST requests only
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=403)
        try:
            data = request.data # A json input matching the Pair model

            # Check if pair already exists
            pair_id = data.get("pair_id")
            if Pair.objects.filter(pair_id=pair_id).exists():
                return Response({"error": f"Pair {pair_id} already exists"}, status=400)

            # Generate uid automatically (max existing + 1)
            max_uid = Pair.objects.aggregate(models.Max("uid"))["uid__max"]
            next_uid = (max_uid or 0) + 1

            # Create new pair
            pair = Pair(
                uid=next_uid,
                pair_id=pair_id,
                pool_contracts=data.get("pool_contracts", {}),
                base_token=data.get("base_token"),
                quote_token=data.get("quote_token"),
                base_token_decimals=data.get("base_token_decimals", 18),
                quote_token_decimals=data.get("quote_token_decimals", 18),
                active_exchanges=data.get("active_exchanges", []),
            )
            pair.save()

            return Response(
                {"message": f"Created pair {pair.pair_id}", "pair_id": pair.pair_id},
                status=201,
            )
        
        # fail gracefully and provide a clear status code so that it is clear the operation failed.
        except Exception as e:
            return Response({"error": str(e)}, status=400)
```

--- Please be aware that if you would like to continue building on this project towards production it would make sense to make additional models called Token, Exchange and Pool so you can nest them and work in a nicely reffered and json Typed environment.

## Querying the prices from the chain

First, lets add some packages that we will need from now on: `poetry add web3 retry python-dotenv`

Now that we have our API skeleton and data model set up, let's dive into the core functionality - actually fetching prices from different blockchain DEXs. The challenge here is that we're dealing with multiple blockchains (Ethereum, Aptos) and multiple DEX protocols (Uniswap, Hyperion), each with their own quirks and data formats.

### The Orchestrator

To solve the multi-faceted complexity we will use an orchetstrator, the `get_token_price()` function in `queries.py`. It will take in the pair from the request, fetch the needed data from the model/backend and then query the correct chain using a mapping between the exchange variable of the pair and its associated price_query function like this. The below function makes heavy use of `Enum` setups from `validation.py` so we can be assured of the correct values being referenced for network and exchange naming in-line with our django model.

```python
def get_token_price(token_pair: str) -> Dict:
    # Fetch the pair configuration from database and loop through each exchange for that pair
    pair = Pair.objects.get(pair_id=token_pair)
    prices = {}
    for exchange_id in pair.active_exchanges:
        # Get the right query function for this exchange and RPC for this network
        query_func = EXCHANGE_QUERY_FUNCTIONS[exchange_id]
        network = Exchange.get_network(exchange_id) # get value from Enum
        rpc_url = os.getenv(f"{network.upper()}_RPC_URL") # match enum with naming in .env
        
        # Query the exchange and collect results
        price = query_func(pair, rpc_url)
        if price is not None:
            prices[exchange_id] = price
    
    # 6. Return aggregated results with best price
    return {
        "token_pair": pair.pair_id,
        "best_price": min(prices.values()),
        "prices": prices # fails gracefully as prices will be empty if query to exchanges fails
    }
```

We define the RPC_urls in our .env where the RPC urls are safe as django is a server-side setup where users dont see the blockchain requests themselves. You can get free RPCs for development from the docs of your favourite chain.

```
MAINNET_RPC_URL=https://eth-mainnet.public.blastapi.io
APTOSMAINNET_RPC_URL=https://fullnode.mainnet.aptoslabs.com
```

The mapping of the function looks like this so that we can support both the Hyperion and the Uniswap dex with separate queries without patternmatching or complex if/else statements in the larger get_token_price function. The Exchange enum (defined in `validation.py`) provides the valid exchange IDs and their associated networks:

```python
class Exchange(Enum):
    UNISWAP = ("uniswap", Network.ETHEREUM)
    HYPERION = ("hyperion", Network.APTOS)
```

```python
EXCHANGE_QUERY_FUNCTIONS = {
    Exchange.UNISWAP.id: query_uniswap_price,
    Exchange.HYPERION.id: query_hyperion_price,
}
```

## Exchange-specific price functions

To complete our setup and project we need to implement the functions to query the specific blockchain which we will do in two ways to show what is standard/possible in web3.

Different blockchains require different connection methods or web-framework standards. For example EVM chains follow the json-RPC framework for Get/Post requests while Cosmos blockchain are known for their extensive gRPC support and Move blockchains like Sui and Aptos rely largely on REST. Additionally each blockchain has their own SDKs and other tooling to "simplify" using these query methods which doesn't always make everything simpler when building crosschain. Packages can be a drain on compiling times, version handling and change very rapidly. API implementations are relaively programmatic though and very well documented when changed which makes implementation easier in the long run.

To show you how this works we will implement:
- **EVM chains (Ethereum)**: Use Web3.py SDK with JSON-RPC to show a package use
- **Aptos**: Use barebones REST API endpoints without SDK to show normal use

The orchestrator handles the setup for the different networks by:
1. Looking up which network an exchange operates on
2. Getting the appropriate RPC/API URL from environment variables
3. Passing both the pair data and connection URL to the exchange-specific function
4. Deliver a standardised output JSON with price as a float

```json
{
    "token_pair": "WBTCUSDC",
    "best_price": 118873.62,
    "prices": {
        "uniswap": 118993.52,
        "hyperion": 118873.62
    }
}
```

As mentioned above the function fails gracefully meaning if an exchange query doesn't give a proper price its left out, if no price is found an error is issued with proper status code.

### Querying Uniswap V3 (Ethereum)

Uniswap V3 stores is a concentrated limit order book exchange meaning the place where bids meet is the current price. This "tick" price might not be the exact price a user gets their tokens at when swapped as it doesn't account for slippage which is where a trader sells/buys more tokens than are bought/sold by a single bidder on the other side forcing the trade to another bidder with a different price to complete the offer. 

Uniswap therefore stores the current estimate not accounting for slippage in the `slot0` function. It is stored here in a specific format for efficiency sake (storage and compute on a blockchain costs a lot) which we can decipher using some basic math as shown below.

We use Web3 as an SDK to wrap an RPC and the Smart-contract function definition called an "ABI" so we can call them as methods. You can download the ABI for any specific contract from Etherscan or deterministically derive it from the source-code if that is available.

```python
def query_uniswap_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Uniswap for token pair price."""
    # Get the pool contract address from our pair configuration
    pool_address = pair.pool_contracts.get("uniswap")
    
    # Connect to Ethereum via Web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    
    # Load the minimal ABI we need (just slot0 function)
    with open("uniswap_pool_abi.json", "r") as abi_file:
        pool_abi = json.load(abi_file)
    
    pool_contract = web3.eth.contract(
        address=Web3.to_checksum_address(pool_address), 
        abi=pool_abi
    )
    
    # Call slot0() to get the current pool state
    slot0 = pool_contract.functions.slot0().call()
    sqrt_price_x96 = int(slot0[0])  # First value is sqrtPriceX96
```
The price encoding of Uniswap is as follows:
- Prices are stored as `sqrtPriceX96` - the square root of the price, multiplied by 2^96
- This is a Q64.96 fixed-point format used for precision without floating point math
- To get the actual price: `(sqrtPriceX96 / 2^96)^2`

Besides this we also have to account for the difference in decimals between tokens which is the INT-->Float conversion blockchains use we spoke about earlier. You can find the decimals for a specific token on their contract on [etherscan](https://etherscan.io/token/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48#readProxyContract#F11).

```python
    # Convert from Q64.96 format to actual price
    raw_price = (sqrt_price_x96 / (2**96)) ** 2
    
    # Adjust for token decimals (e.g., WBTC has 8, USDC has 6)
    decimal_adjustment = 10 ** (pair.base_token_decimals - pair.quote_token_decimals)
    return raw_price * decimal_adjustment
```

Some additional considerations if you continue developing this API
- Token ordering in Uniswap V3 is deterministic (smaller address (hex ordering) = token0)
- The pooladdress for 2 tokens is also deterministic so you could infer the pool_address to have "permissionless" price querying
- The price represents token0/token1, which may not match your pair ordering if named incorrectly in the model
- There are different fee rates for every pool and ofcourse slippage so for a full price breakdown you would have to simulate an actual quote based on trading size

You can find more information about this more complex querying approach on the [Uniswap Docs](https://docs.uniswap.org/sdk/v3/guides/swaps/quoting).

### Querying Hyperion (Aptos)

For Hyperion on Aptos, we take a different approach - using REST APIs directly without an SDK. Aptos uses a specific naming to accces any and all contract through something called a [view function](https://fullnode.mainnet.aptoslabs.com/v1/spec#/operations/view). the nomenclature is: `CONTRACT::method::function``. So going to the [hyperion docs](https://docs.hyperion.xyz/developer/via-contract) and referencing their main contract address we can see all methods and functions on the Aptos [blockchain explorer](https://explorer.aptoslabs.com/object/0x8b4a2c4bb53857c718a04c020b98f8c2e1f99a68b0f57389a8bf5434cd22e05c/modules/code/pool_v3?network=mainnet) and define the query we need.


Let us now use a simple Json + request structure to query this REST endpoint. You can reference this `request_json` function implementation with Retry decorator in `queries.py`.
```python
def query_hyperion_price(pair: Pair, rpc_url: str) -> Optional[float]:
    """Query Hyperion pool resource to get sqrt_price directly."""
    # Get the pool account address
    pool_address = pair.pool_contracts.get("hyperion")
    
    # Construct the resource URL for the LiquidityPoolV3 struct
    resource_url = f"{rpc_url}/v1/accounts/{pool_address}/resource/{CONTRACT}::pool_v3::LiquidityPoolV3"
    
    # Make a simple GET request
    resource_data = request_json(resource_url)
    sqrt_price = int(resource_data["data"]["sqrt_price"])
```

You will see that basically all exchanges take heavy inspiration from uniswap. This is clear from the order-book implementation to the data they provide in their endpoints. So for Hyperion a similar price encoding takes place and again we are getting the current price between the buy/sell ticks and not accounting for slippage/fees.

Hyperion Uses x64 fixed-point (not Q64.96) changing the formula to `(sqrt_price / 2^64)^2`
```python
    # Convert from x64 fixed-point to actual price
    raw_price = (sqrt_price / (2**64)) ** 2
    
    # Same decimal adjustment as Uniswap
    decimal_adjustment = 10 ** (pair.base_token_decimals - pair.quote_token_decimals)
    return raw_price * decimal_adjustment
```

# Data ingestion and testing

Now it's time to test our entire project by starting our database/API through a development server and ingesting some sample data. We will also create some simple tests that can run on Django locally to verify that our setup is working and have some consistency to fall back to when we add to the project over time.

## Setting up the Django Database

Before we can run our API, Django needs to create the database tables for our models. This is done through Django's migration system:

```bash
# Create migration files for our Pair model
cd dex_agg_tutorial
poetry run python manage.py makemigrations core

# Apply the migrations to create actual database tables
poetry run python manage.py migrate
```

The first command analyzes your models and creates migration files that describe what database changes need to be made. The second command actually applies those changes to create the SQLite database file.

You should see output like:
```
Migrations for 'core':
  dex_agg_tutorial/core/migrations/0001_initial.py
    + Create model Pair
```
You can remove the migrations and db file at any time to be able to re-init the local database.

## Creating an Admin User

To create and manage token pairs through the Django admin interface, you'll need an admin user:

```bash
poetry run python manage.py createsuperuser
```

This will prompt you for a username, email, and password. Choose something secure but memorable for local development.

## Starting the Development Server

Now you can start the Django development server:

```bash
poetry run python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`. You can visit:
- `http://127.0.0.1:8000/` - Welcome message
- `http://127.0.0.1:8000/pairs/` - List of token pairs
- `http://127.0.0.1:8000/admin/` - Django admin interface
- `http://127.0.0.1:8000/price/PAIRID/` - Price for a specific pair

## Adding Sample Data

We've created a sample dataset in `core/tests/sample_pairs.json` with real pool addresses for testing:

```json
[
  {
    "pair_id": "WBTCUSDC", 
    "base_token": "WBTC",
    "quote_token": "USDC",
    "base_token_decimals": 8,
    "quote_token_decimals": 6,
    "active_exchanges": ["uniswap", "hyperion"],
    "pool_contracts": {
      "uniswap": "0x99ac8ca7087fa4a2a1fb6357269965a2014abc35",
      "hyperion": "0xa7bb8c9b3215e29a3e2c2370dcbad9c71816d385e7863170b147243724b2da58"
    }
  }
]
```

You can add this data through the API using curl with your admin credentials:

```bash
# Load all sample pairs (requires jq)
cat core/tests/sample_pairs.json | jq -c '.[]' | while read pair; do
  echo "Adding pair: $(echo $pair | jq -r '.pair_id')"
  curl -X POST http://127.0.0.1:8000/pairs/ \
    -H "Content-Type: application/json" \
    -u admin:yourpassword \
    -d "$pair"
done
```

Or add them individually if you don't have `jq` installed:

```bash
curl -X POST http://127.0.0.1:8000/pairs/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{"pair_id": "WBTCUSDC", "base_token": "WBTC", "quote_token": "USDC", "base_token_decimals": 8, "quote_token_decimals": 6, "active_exchanges": ["uniswap", "hyperion"], "pool_contracts": {"uniswap": "0x99ac8ca7087fa4a2a1fb6357269965a2014abc35", "hyperion": "0xa7bb8c9b3215e29a3e2c2370dcbad9c71816d385e7863170b147243724b2da58"}}'
```

## Testing with Real Blockchain Data

Once you have pairs loaded, you can test price queries. You'll need RPC URLs in your `.env` file:

```env
MAINNET_RPC_URL=https://eth-mainnet.public.blastapi.io
APTOSMAINNET_RPC_URL=https://fullnode.mainnet.aptoslabs.com
```

Then query prices:

```bash
curl http://127.0.0.1:8000/price/WBTCUSDC/
```

You should get real price data:

```json
{
    "token_pair": "WBTCUSDC",
    "best_price": 118873.62,
    "prices": {
        "uniswap": 118993.52,
        "hyperion": 118873.62
    }
}
```

## Automated Testing

Testing is crucial for any codebase but especially for APIs and backend integration. Testing ensures your code works correctly and catches issues early. Let's create a few simple tests to validate some of the aggregator functionality.

### Setting Up Test Structure

Django tests go in a `tests/` directory within your app and can also be called with the django `manage.py` structure meaning it has proper access to all the models and objects we created. You can find all tests we created in this tutorial in `core/tests/test_pricing.py`.

Here is some explanation of how testing works and what you can do with it. If you are unfamiliar with testing in general or testing in django then we would highly recommend you check out the following [video tutorial](https://www.youtube.com/watch?v=la69esudPYY).
```python
import os
import json
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User

from core.models import Pair
from core.queries import get_token_price
```

### Test 1: Basic Model Creation

Start with testing your Django model works correctly:

```python
class ModelTest(TestCase):
    """Basic model functionality tests."""
    
    def test_pair_model_creation(self):
        """Test Pair model creation and properties."""
        pair = Pair.objects.create(
            uid=1,
            pair_id="TESTPAIR",
            base_token="TEST",
            quote_token="USD",
            base_token_decimals=18,
            quote_token_decimals=6,
            active_exchanges=["uniswap"],
            pool_contracts={"uniswap": "0x123"}
        )
        
        # Verify the pair was created correctly
        self.assertEqual(pair.pair_id, "TESTPAIR")
        self.assertTrue(pair.is_active)
        self.assertEqual(len(pair.active_exchanges), 1)
        self.assertIn("uniswap", pair.pool_contracts)
```

This test:
- Creates a test pair with known data
- Verifies all fields are stored correctly
- Tests the `is_active` property logic

### Test 2: API Endpoint Testing

Test your REST API endpoints work as expected:

```python
class PairAPITest(APITestCase):
    """Test API with real sample data."""
    
    def setUp(self):
        """Load sample pairs and create admin."""
        # Create admin user for authentication
        self.admin = User.objects.create_superuser(
            username="admin", password="testpass"
        )
        
        # Load your sample JSON data
        sample_file = os.path.join(os.path.dirname(__file__), "sample_pairs.json")
        with open(sample_file, "r") as f:
            self.sample_pairs = json.load(f)
        
        # Create pairs in test database
        for i, pair_data in enumerate(self.sample_pairs, 1):
            Pair.objects.create(uid=i, **pair_data)
    
    def test_list_pairs(self):
        """Test GET /pairs/ returns all sample pairs."""
        response = self.client.get("/pairs/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), len(self.sample_pairs))
        
        # Check that all our sample pairs are present
        pair_ids = [pair["pair_id"] for pair in response.data]
        expected_ids = [pair["pair_id"] for pair in self.sample_pairs]
        for expected_id in expected_ids:
            self.assertIn(expected_id, pair_ids)
```

This test:
- Sets up sample data from your JSON file
- Tests the GET endpoint returns correct data
- Verifies all expected pairs are included

### Test 3: Authentication and Authorization

Test that admin-only endpoints are properly secured:

```python
def test_create_pair_requires_admin(self):
    """Test POST /pairs/ requires admin auth."""
    new_pair = {
        "pair_id": "LINKUSDC",
        "base_token": "LINK",
        "quote_token": "USDC",
        "base_token_decimals": 18,
        "quote_token_decimals": 6,
        "active_exchanges": ["uniswap"],
        "pool_contracts": {"uniswap": "0x1234567890abcdef"},
    }
    
    # Without authentication - should fail
    response = self.client.post("/pairs/", new_pair, format="json")
    self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    # With admin authentication - should succeed
    self.client.force_authenticate(user=self.admin)
    response = self.client.post("/pairs/", new_pair, format="json")
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    # Verify the pair was actually created
    get_response = self.client.get("/pairs/")
    pair_ids = [pair["pair_id"] for pair in get_response.data]
    self.assertIn("LINKUSDC", pair_ids)
```

This test:
- Attempts to create a pair without authentication (should fail)
- Creates a pair with admin auth (should succeed)
- Verifies the pair actually appears in the database

### Test 4: Price Query Structure

Test that price endpoints return the correct data structure:

```python
def test_price_endpoint_structure(self):
    """Test that price endpoints return correct structure."""
    for sample_pair in self.sample_pairs:
        pair_id = sample_pair["pair_id"]
        response = self.client.get(f"/price/{pair_id}/")
        
        # Should return 200 and have correct structure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token_pair", response.data)
        self.assertEqual(response.data["token_pair"], pair_id)
        
        # If we got actual prices, verify best_price logic
        if "prices" in response.data and "best_price" in response.data:
            prices = response.data["prices"]
            best_price = response.data["best_price"]
            
            # best_price should be the minimum of all exchange prices
            if prices:
                expected_best = min(prices.values())
                self.assertEqual(best_price, expected_best)
```

This test:
- Queries all sample pairs for prices
- Verifies response structure is consistent
- Tests the best_price calculation logic
- Works regardless of whether RPC URLs are configured

### FINAL: Integration Test with Real Data

Lastly we buily a small integration test that uses real data and actually queries the blockchain. Normally We would advise to do this as a full continuous integration through github workflows but that is a bit too much for this tutorial as setting up Django in CI is quite the task.

```python
def test_pricing_function_calls(self):
    """Test that pricing functions can be called with real data."""
    pairs = Pair.objects.all()
    
    for pair in pairs:
        # Call the main pricing function
        result = get_token_price(pair.pair_id)
        
        # Should always return a dict with token_pair
        self.assertIsInstance(result, dict)
        self.assertIn("token_pair", result)
        self.assertEqual(result["token_pair"], pair.pair_id)
        
        if "error" in result:
            print(f"{pair.pair_id}: {result['error']}")
            # This is expected if we don't have RPC URLs configured
        else:
            # We got actual prices! Validate them
            self.assertIn("best_price", result)
            self.assertIn("prices", result)
            
            # Basic sanity checks for known pairs
            if pair.pair_id == "WBTCUSDC":
                # BTC should be > $10,000 
                self.assertGreater(result["best_price"], 10000)
            
            print(f"✓ {pair.pair_id}: {result['best_price']}")
```

This test:
- Uses real sample data with actual pool addresses
- Makes actual blockchain calls using the RPCs from .env
- Validates price ranges make sense
- Fails gracefully when blockchain access isn't configured

### Running Your Tests

Execute your tests with:

```bash
poetry run python manage.py test core.tests.test_pricing
```

Example output:
```
✓ WBTCUSDC: WBTC(8) / USDC(6) on ['uniswap', 'hyperion']
--- Testing WBTCUSDC ---
✓ WBTCUSDC: Best price = 118873.62
  uniswap: 118993.52
  hyperion: 118873.62
----------------------------------------------------------------------
Ran 7 tests in 1.995s

OK
```

WE KNOW TESTING IS BORING. BUT PLEASE TEST AND BE HAPPY :)

ps. If you don't like testing, subscribe to claude or gemini and kindly ask them to help you.

# Conclusion

Congratulations! You've successfully built a working multi-blockchain DEX aggregator from scratch. What you have now is a solid foundation that can actually query real prices from live exchanges across different blockchains. That's pretty cool, right?

So what is working right now?
- The API can actually fetch real Bitcoin and Aptos prices from live pools
- There is an active Django model that can be extended for proper data consistency
- Two completely different blockchain architectures (EVM vs Move) are handled

But here's the thing - building a production DEX aggregator involves way more complexity than what we've covered. Throughout this tutorial, I've mentioned several considerations that are crucial for real-world usage. Let's be honest about what's still missing:

Right now you're getting the "current price" from each pool, but that's not what users will actually pay. Real trades involve:
- **Slippage calculation** - larger trades move the price against you
- **Fee calculation** - each pool has different fee rates 
- **Multi-hop routing** - sometimes the best price requires going through multiple pools
- **MEV considerations** - your transaction might get front-run

Your current setup requires manually adding each token pair, but in reality you will have to dynamically find pools for users as they are created constantly. These pools also need to be validated to not be scam tokens. You can start on this by deterministically getting the pool contract addresses for Uniswap for example using the token0/token1 addresses. This also solves your ordering problem so all assets are quoted in the logical asset (USD). Then saving this data into separate Token, Exchange and Network models would really help you manage the correct style of data and reference pairs against their correct exchange, network and token.

But you will also run into issues like people abusing your APIs which fire of queries to a blockchain every time they are called, this is highly ineffecient and might create big server or RPC partner bills for you. So caching, proper user management and more like this will 100% be required to move this into production.

## Final Thoughts

We hope you enjoyed scrolling through, building on or laughing about this tutorial. Surely there were some things you picked up from it :) 

We are open to commits if you want to extend the tutorial or base-app and learn more about Django and Crypto backend-development.