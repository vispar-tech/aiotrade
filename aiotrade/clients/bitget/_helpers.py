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
        # each item (dict) is an account, with field "marginCoin"/"usdtEquity"
        accounts = resp.get("data", [])
        for account in accounts:
            # Use the outer account's marginCoin to match the asset
            margin_coin = account.get("marginCoin")
            if margin_coin == asset:
                usdt_equity = account.get("usdtEquity")
                if usdt_equity is None:
                    continue
                try:
                    return float(usdt_equity)
                except Exception:
                    logger.warning(
                        "`usdtEquity` is not parseable as float: %r", usdt_equity
                    )
                    return None
        return None
