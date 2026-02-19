import logging
from typing import Any

logger = logging.getLogger(__name__)


class BybitHelpers:
    """Utility/helper methods for BybitClient."""

    @staticmethod
    def extract_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance for a specific coin.

        Accepts response from Bybit API get_wallet_balance.

        Args:
            resp: The API response dictionary to parse.
            asset: Ticker symbol (e.g., "USDT", "BTC") to extract.

        Returns:
            The wallet balance as a float, or None if not found.
        """
        # Try "result" key, fallback to root for raw list responses
        accounts = (
            resp.get("result", {}).get("list") if "result" in resp else resp.get("list")
        )
        if not accounts:
            return None

        for account in accounts:
            coins = account.get("coin", [])
            for coin in coins:
                if coin.get("coin") == asset:
                    balance = coin.get("walletBalance")
                    if balance is None:
                        return None
                    try:
                        return float(balance)
                    except Exception:
                        return None
        return None
