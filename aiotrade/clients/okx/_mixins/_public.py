from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol


class PublicMixin:
    """Mixin for account endpoints."""

    async def get_instruments(
        self: HttpClientProtocol,
        inst_type: Literal["SPOT", "MARGIN", "SWAP", "FUTURES", "OPTION"],
        inst_family: str | None = None,
        inst_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve a list of instruments with open contracts for OKX.

        See:
            https://www.okx.com/docs-v5/en/#public-data-rest-api-get-instruments.

        Args:
            inst_type: Instrument type.
                SPOT: Spot
                MARGIN: Margin
                SWAP: Perpetual Futures
                FUTURES: Expiry Futures
                OPTION: Option
            inst_family: Instrument family.
                Only required for FUTURES/SWAP/OPTION.
                If instType is OPTION, instFamily is required.
            inst_id: Instrument ID.

        Returns:
            Dict with instruments information.
        """
        params: dict[str, str] = {"instType": inst_type}
        if inst_family is not None:
            params["instFamily"] = inst_family
        if inst_id is not None:
            params["instId"] = inst_id
        return await self.get(
            "/api/v5/public/instruments",
            params=params,
            auth=False,
        )

    async def get_position_tiers(
        self: HttpClientProtocol,
        inst_type: Literal["MARGIN", "SWAP", "FUTURES", "OPTION"],
        td_mode: Literal["cross", "isolated"],
        inst_family: str | None = None,
        inst_id: str | None = None,
        ccy: str | None = None,
        tier: str | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve position tiers information, max leverage, maintenance margin, etc.

        See:
            https://www.okx.com/docs-v5/en/#public-data-rest-api-get-position-tiers

        Args:
            inst_type: Instrument type. Required. One of MARGIN, SWAP, FUTURES, OPTION.
            td_mode: Trade mode. Required. Either "cross" or "isolated".
            inst_family: Instrument family. Conditional.
                Required for SWAP/FUTURES/OPTION.
            inst_id: Instrument ID. Conditional. No more than 5 (comma-separated).
                Either inst_id or ccy is required. If both present, inst_id is used.
                If inst_type is SWAP/FUTURES/OPTION, ignored.
            ccy: Margin currency for cross MARGIN only. Conditional.
            tier: Tiers. Optional.

        Returns:
            Dict with position tiers response data.
        """
        params: dict[str, str] = {
            "instType": inst_type,
            "tdMode": td_mode,
        }
        if inst_family is not None:
            params["instFamily"] = inst_family
        if inst_id is not None:
            params["instId"] = inst_id
        if ccy is not None:
            params["ccy"] = ccy
        if tier is not None:
            params["tier"] = tier

        return await self.get(
            "/api/v5/public/position-tiers",
            params=params,
            auth=False,
        )
