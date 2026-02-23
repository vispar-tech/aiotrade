import logging
from typing import Any

logger = logging.getLogger(__name__)


class OkxHelpers:
    """Utility/helper methods for OkxClient."""

    @staticmethod
    def extract_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance for a specific coin (e.g., "USDT").

        Handles both standard responses and raw "data" structure.

        Args:
            resp: API response dictionary.
            asset: Asset/currency symbol, e.g., "USDT", "BTC". Default: "USDT".

        Returns:
            Wallet balance as float if found, else None.
        """
        # Prefer v5 "data" field (list of accounts with details)
        accounts = resp.get("data", [])

        for account in accounts:
            # v5: balances in "details" list, each as a dict
            details = account.get("details", [])
            for detail in details:
                # Look for the matching currency
                if detail.get("ccy") == asset:
                    balance = detail.get("eq")
                    if balance is None:
                        continue
                    try:
                        return float(balance)
                    except Exception:
                        return None
        return None
