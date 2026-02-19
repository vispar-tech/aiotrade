import logging
from typing import Any

logger = logging.getLogger(__name__)


class BingxHelpers:
    """Utility/helper methods for BingxClient."""

    @staticmethod
    def extract_swap_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the wallet balance for a specific asset.

        Accepts response from BingX API (swap account balance).

        Note:
            If the account is in demo, you should use asset="VST" instead of "USDT".

        Args:
            resp: The API response dictionary to parse. Expects resp["data"].
            asset: Ticker symbol (e.g., "USDT", "VST") to extract.

        Returns:
            The wallet balance as a float, or None if not found.
        """
        # "data" key must be a list of account balance dicts
        balances = resp.get("data", [])
        if not balances:
            return None

        for entry in balances:
            # Each entry is expected to be a dict
            # with keys such as "asset" and "balance"
            if entry.get("asset") == asset:
                balance = entry.get("balance")
                if balance is None:
                    return None
                try:
                    return float(balance)
                except Exception:
                    return None
        return None

    @staticmethod
    def extract_spot_wallet_balance(
        resp: dict[str, Any], asset: str = "USDT"
    ) -> float | None:
        """
        Extract the spot wallet balance (sum of free + locked) for a specific asset.

        Accepts response from BingX API (spot account assets).

        Note:
            BingX demo accounts do NOT support SPOT trading.
            This means spot wallet balances are always returned from MAINNET.

        Args:
            resp: The API response dictionary. Expects resp["data"]["balances"].
            asset: Ticker symbol (e.g., "USDT", "BTC") to extract.

        Returns:
            The sum of free and locked as a float, or None if not found.
        """
        balances = resp.get("data", {}).get("balances", [])
        if not balances:
            return None

        for entry in balances:
            if entry.get("asset") == asset:
                free = entry.get("free")
                locked = entry.get("locked")
                if free is None or locked is None:
                    return None
                try:
                    return float(free) + float(locked)
                except Exception:
                    return None
        return None
