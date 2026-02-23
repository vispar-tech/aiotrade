import logging
from typing import Any

logger = logging.getLogger(__name__)


class BitgetHelpers:
    """Utility/helper methods for BitgetClient."""

    @staticmethod
    def extract_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance for a specific coin.

        Accept Bitget's account list API response.

        Args:
            resp: API response dictionary.
            asset: Asset/currency symbol, e.g., "USDT", "BTC". Default: "USDT".

        Returns:
            Wallet balance as float if found, else None.
        """
        # The v5 futures/spot account API for Bitget returns a list under "data",
        # each item (dict) is an account, with field "marginCoin"/"accountEquity"
        accounts = resp.get("data", [])
        for account in accounts:
            # Use the outer account's marginCoin to match the asset
            margin_coin = account.get("marginCoin")
            if margin_coin == asset:
                account_available = account.get("available")
                if account_available is None:
                    continue
                try:
                    return float(account_available)
                except Exception:
                    logger.warning(
                        "`available` is not parseable as float: %r", account_available
                    )
                    return None
        return None
