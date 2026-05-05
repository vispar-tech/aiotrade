import logging
from typing import Any

logger = logging.getLogger(__name__)


class KuCoinHelpers:
    """Utility/helper methods for KuCoinClient."""

    @staticmethod
    def extract_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance (accountEquity) for futures account response.

        Args:
            resp: API response dictionary.
            asset: Asset/currency symbol, e.g., "USDT", "BTC". Default: "USDT".

        Returns:
            Wallet balance as float if found, else None.
        """
        data = resp.get("data", {})
        currency = data.get("currency")
        if currency != asset:
            return None
        margin_balance = data.get("marginBalance")
        if margin_balance is None:
            return None
        try:
            return float(margin_balance)
        except Exception:
            logger.warning(
                "`marginBalance` is not parseable as float: %r", margin_balance
            )
            return None
