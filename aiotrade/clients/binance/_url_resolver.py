class BinanceUrlResolver:
    """URL resolver for Binance endpoints."""

    API_URL = "https://api.binance.com"
    API_DEMO_URL = "https://demo-api.binance.com"
    # c
    FUTURES_URL = "https://fapi.binance.com"
    FUTURES_DEMO_URL = "https://demo-fapi.binance.com"
    # COIN
    FUTURES_COIN_URL = "https://dapi.binance.com"
    FUTURES_COIN_DEMO_URL = "https://demo-dapi.binance.com"

    @staticmethod
    def resolve(is_demo: bool, endpoint: str) -> str:
        if "fapi" in endpoint:
            return (
                BinanceUrlResolver.FUTURES_DEMO_URL
                if is_demo
                else BinanceUrlResolver.FUTURES_URL
            )
        if "dapi" in endpoint:
            return (
                BinanceUrlResolver.FUTURES_COIN_DEMO_URL
                if is_demo
                else BinanceUrlResolver.FUTURES_COIN_URL
            )
        return (
            BinanceUrlResolver.API_DEMO_URL if is_demo else BinanceUrlResolver.API_URL
        )
