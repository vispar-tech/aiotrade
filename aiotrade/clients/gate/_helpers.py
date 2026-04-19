import logging
from typing import Any

logger = logging.getLogger(__name__)


class GateHelpers:
    """Utility/helper methods for GateClient."""

    @staticmethod
    def extract_wallet_balance(resp: dict[str, Any]) -> float | None:
        """
        Calculate the full wallet balance from Gate USDT futures response:
        available + isolated_position_margin + cross_initial_margin.

        Args:
            resp: API response dictionary.
            asset: Not used; kept for interface compatibility.

        Returns:
            Full wallet balance as float if all fields found, else None.
        """  # noqa: D205
        result: dict[str, Any] = resp.get("result", {})
        if not result:
            return None

        available = result.get("available")
        isolated_position_margin = result.get("isolated_position_margin")
        cross_initial_margin = result.get("cross_initial_margin")

        if available is None:
            return None

        try:
            return (
                float(available)
                + float(isolated_position_margin or 0)
                + float(cross_initial_margin or 0)
            )
        except Exception as e:
            logger.error("Failed to parse one of balance components: %s", e)
            return None
