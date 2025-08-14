import requests
from retry import retry

from validation import BadRequestException


@retry(BadRequestException, delay=10, tries=2)
def request_json(url: str) -> dict:
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    else:
        raise BadRequestException(f"Status Code: {r.status_code} | {url}")


def get_token_price(token_pair):
    return 1e6
