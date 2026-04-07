import logging
from typing import Any

logger = logging.getLogger(__name__)


class BinanceHelpers:
    """Utility/helper methods for BinanceClient."""

    @staticmethod
    def extract_futures_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance for a specific asset (e.g., "USDT").

        Args:
            resp: API response dictionary.
            asset: Asset/currency symbol, e.g., "USDT", "BTC". Default: "USDT".

        Returns:
            Wallet balance as float if found, else None.
        """
        accounts = resp.get("result", {}).get("list", [])
        if accounts is None:
            return None

        for account in accounts:
            if account.get("asset") == asset:
                balance = account.get("balance")
                if balance is None:
                    continue
                try:
                    return float(balance)
                except Exception:
                    return None
        return None

    @staticmethod
    def prepend_broker_id(
        broker_id: str | None, order_link_id: str, max_length: int = 36
    ) -> str:
        """Add binance broker id to order link id."""
        if broker_id is not None:
            return ("x-" + broker_id + "-" + order_link_id)[:max_length]
        return order_link_id
