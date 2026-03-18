from typing import Literal

GLOBAL_API_ENDPOINT = "https://api.kucoin.com"
GLOBAL_FUTURES_API_ENDPOINT = "https://api-futures.kucoin.com"
GLOBAL_BROKER_API_ENDPOINT = "https://api-broker.kucoin.com"


def base_url(kind: Literal["spot", "futures", "broker"]) -> str:
    if kind == "spot":
        return GLOBAL_API_ENDPOINT
    if kind == "futures":
        return GLOBAL_FUTURES_API_ENDPOINT
    if kind == "broker":
        return GLOBAL_BROKER_API_ENDPOINT
    raise ValueError(f"Unknown KuCoin API kind: {kind!r}")
