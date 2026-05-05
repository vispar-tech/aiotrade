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
                # Sum of unionAvailable + isolatedMargin + crossedMargin
                try:
                    ua = float(account.get("unionAvailable", 0) or 0)
                except Exception:
                    logger.warning(
                        "`unionAvailable` is not parseable as float: %r",
                        account.get("unionAvailable"),
                    )
                    ua = 0.0
                try:
                    im = float(account.get("isolatedMargin", 0) or 0)
                except Exception:
                    logger.warning(
                        "`isolatedMargin` is not parseable as float: %r",
                        account.get("isolatedMargin"),
                    )
                    im = 0.0
                try:
                    cm = float(account.get("crossedMargin", 0) or 0)
                except Exception:
                    logger.warning(
                        "`crossedMargin` is not parseable as float: %r",
                        account.get("crossedMargin"),
                    )
                    cm = 0.0
                return ua + im + cm
        return None

    @staticmethod
    def extract_available_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the abailable wallet balance for a specific coin.

        Accept Bitget's account list API response.

        Args:
            resp: API response dictionary.
            asset: Asset/currency symbol, e.g., "USDT", "BTC". Default: "USDT".

        Returns:
            Available wallet balance as float if found, else None.
        """
        # The v5 futures/spot account API for Bitget returns a list under "data",
        # each item (dict) is an account, with field "marginCoin"/"usdtEquity"
        accounts = resp.get("data", [])
        for account in accounts:
            # Use the outer account's marginCoin to match the asset
            margin_coin = account.get("marginCoin")
            if margin_coin == asset:
                available = account.get("available")
                if available is None:
                    continue
                try:
                    return float(available)
                except Exception:
                    logger.warning(
                        "`available` is not parseable as float: %r", available
                    )
        return None
