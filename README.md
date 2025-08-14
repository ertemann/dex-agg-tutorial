# DEX Aggregator Tutorial

A Tutorial to build a DEX aggregator in Python using Django that supports price queries across multiple exchanges (Uniswap on Ethereum and Hyperion on Aptos).

The below information will help you setup a local development server to test and work on the endpoints. There is no production-ready setup information available as this project is not intended for production use. If you want to utilize this project to build a production-ready dex API we suggest to use a docker container to build and host the Django server and a platform like Vercel or Fly to host the database redundantly.

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Run migrations:
```bash
cd dex_agg_tutorial
poetry run python manage.py migrate
```

3. Create admin user:
```bash
poetry run python manage.py createsuperuser
```

## Running the Server

```bash
cd dex_agg_tutorial
poetry run python manage.py runserver
```

Server will be available at `http://127.0.0.1:8000/`

## API Endpoints

- `GET /` - Welcome message
- `GET /pairs/` - List all token pairs
- `POST /pairs/` - Create new pair (admin only)
- `GET /price/{pair_id}/` - Get price for token pair

## Adding Sample Data

To add all sample pairs from `tests/sample_pairs.json` at once, use this bash script (Adjust the admin username and password):

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

Or add them one by one using the following command

```bash
# WBTC/USDC pair
curl -X POST http://127.0.0.1:8000/pairs/ \
  -H "Content-Type: application/json" \
  -u admin:yourpassword \
  -d '{"pair_id": "WBTCUSDC", "base_token": "WBTC", "quote_token": "USDC", "active_exchanges": ["uniswap", "hyperion"], "pool_contracts": {"uniswap": "0x99ac8ca7087fa4a2a1fb6357269965a2014abc35", "hyperion": "0xa7bb8c9b3215e29a3e2c2370dcbad9c71816d385e7863170b147243724b2da58"}}'

```

## Querying Prices

After adding pairs, you can query their prices:

```bash
curl http://127.0.0.1:8000/price/WBTCUSDC/
```

Example output:
```json
{
    "token_pair": "WBTCUSDC",
    "best_price": 98765.43,
    "prices": {
        "uniswap": 98765.43,
        "hyperion": 98890.21
    }
}
``` 

## Running Tests

```bash
cd dex_agg_tutorial
poetry run python manage.py test core.tests.test_pricing
```

## Code Quality

Pre-push hook runs automatically. Manual checks:
```bash
poetry run black --check .
poetry run ruff check .
```