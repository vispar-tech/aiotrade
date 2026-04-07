from collections.abc import Iterable, Sequence
from typing import Any, Literal

from aiotrade._protocols import HttpClientProtocol
from aiotrade.utils import join_iterable_field


class TradingAccountMixin:
    """Mixin for OKX trading account balance and position endpoints."""

    async def get_balance(
        self: HttpClientProtocol,
        ccy: str | Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve a list of assets (with non-zero balance) in the trading account.

        Rate Limit: 10 requests per 2 seconds (per User ID)
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-balance

        Args:
            ccy: Single currency or multiple currencies (comma-separated, up to 20),
                 e.g. "BTC", "BTC,ETH", or a list like ["BTC","ETH"].
                 If omitted, returns all assets with non-zero balance.

        Returns:
            Dict containing the wallet balance response.
        """
        params: dict[str, str] = {}
        if ccy:
            params["ccy"] = join_iterable_field(ccy)
        return await self.get(
            "/api/v5/account/balance",
            params=params,
            auth=True,
        )

    async def get_positions(
        self: HttpClientProtocol,
        inst_type: Literal["MARGIN", "SWAP", "FUTURES", "OPTION"] | None = None,
        inst_id: str | Iterable[str] | None = None,
        pos_id: str | Sequence[str] | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve information on your positions.

        In net mode: shows net positions.
        In long/short mode: shows long or short positions.
        Returns in reverse chronological order using ctime.

        Rate Limit: 10 requests per 2 seconds (per User ID)
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-positions

        Args:
            inst_type: "MARGIN", "SWAP", "FUTURES", or "OPTION".
            inst_id: Instrument ID(s) ("BTC-USDT-SWAP" or ["BTC-USDT-SWAP", ...]).
            pos_id: Position ID(s) ("111222" or ["111222", ...]).

        Returns:
            Dict containing position information.
        """
        params: dict[str, str] = {}
        if inst_type is not None:
            params["instType"] = inst_type
        if inst_id:
            params["instId"] = join_iterable_field(inst_id)
        if pos_id:
            params["posId"] = join_iterable_field(pos_id)

        return await self.get(
            "/api/v5/account/positions",
            params=params,
            auth=True,
        )

    async def get_positions_history(
        self: HttpClientProtocol,
        inst_type: Literal["MARGIN", "SWAP", "FUTURES", "OPTION"] | None = None,
        inst_id: str | None = None,
        mgn_mode: Literal["cross", "isolated"] | None = None,
        position_type: Literal[
            1,  # Close position partially
            2,  # Close all
            3,  # Liquidation
            4,  # Partial liquidation
            5,  # ADL - position not fully closed
            6,  # ADL - position fully closed
        ]
        | None = None,
        pos_id: str | None = None,
        after: int | None = None,
        before: int | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Retrieve the updated position data for the last 3 months.

        Returned in reverse chronological order using utime.

        Rate Limit: 10 requests per 2 seconds (per User ID)
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-positions-history

        Args:
            inst_type: Instrument type. One of
                "MARGIN", "SWAP", "FUTURES", or "OPTION" (optional).
            inst_id: Instrument ID, e.g. "BTC-USD-SWAP" (optional).
            mgn_mode: Margin mode. "cross" or "isolated" (optional).
            position_type: Type of latest close position (optional):
                1: Close position partially
                2: Close all
                3: Liquidation
                4: Partial liquidation
                5: ADL - not fully closed
                6: ADL - fully closed
            pos_id: Position ID (optional).
            after: Return records earlier than requested uTime (ms timestamp,
                optional).
            before: Return records newer than requested uTime (ms timestamp,
                optional).
            limit: Number of results per request (max 100, default 100).

        Returns:
            Dict containing the positions history.
        """
        params: dict[str, Any] = {}
        if inst_type is not None:
            params["instType"] = inst_type
        if inst_id is not None:
            params["instId"] = inst_id
        if mgn_mode is not None:
            params["mgnMode"] = mgn_mode
        if position_type is not None:
            params["type"] = str(position_type)
        if pos_id is not None:
            params["posId"] = pos_id
        if after is not None:
            params["after"] = str(after)
        if before is not None:
            params["before"] = str(before)
        if limit is not None:
            params["limit"] = str(limit)
        return await self.get(
            "/api/v5/account/positions-history",
            params=params,
            auth=True,
        )

    async def set_position_mode(
        self: HttpClientProtocol,
        pos_mode: Literal["long_short_mode", "net_mode"],
    ) -> dict[str, Any]:
        """
        Set position mode.

        FUTURES and SWAP support both long/short mode ("long_short_mode")
        and net mode ("net_mode"). In net mode, users can only have positions
        in one direction; in long/short mode, users can hold both directions.

        Rate Limit: 5 requests per 2 seconds (per User ID)
        Permission: Trade

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-position-mode

        Args:
            pos_mode: "long_short_mode" for long/short, only applicable to FUTURES/SWAP;
                        "net_mode" for net mode.

        Returns:
            Dict containing the result, including the new position mode.
        """
        params = {"posMode": pos_mode}
        return await self.post(
            "/api/v5/account/set-position-mode",
            params=params,
            auth=True,
        )

    async def get_account_config(
        self: HttpClientProtocol,
    ) -> dict[str, Any]:
        """
        Get account configuration.

        Retrieve current account configuration.

        Rate Limit: 5 requests per 2 seconds
        Rate limit rule: User ID
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-account-configuration

        HTTP Request:
            GET /api/v5/account/config

        Args:
            None

        Returns:
            Dict containing the account configuration.
        """
        return await self.get(
            "/api/v5/account/config",
            auth=True,
        )

    async def get_leverage_info(
        self: HttpClientProtocol,
        mgn_mode: Literal["cross", "isolated"],
        inst_id: str | Iterable[str] | None = None,
        ccy: str | Iterable[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get leverage info.

        Retrieve leverage information for instruments or currencies.

        Rate Limit: 20 requests per 2 seconds
        Rate limit rule: User ID
        Permission: Read

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-get-leverage

        HTTP Request:
            GET /api/v5/account/leverage-info

        Args:
            inst_id: (Optional) Instrument ID(s), comma-separated, max 20.
                E.g., "BTC-USDT-SWAP"
            ccy:    (Optional) Currency code(s), comma-separated, max 20.
                Used for currency-level leverage info.
            mgn_mode: (Required) Margin mode. Either "cross" or "isolated".

        Returns:
            Dict containing the leverage info.

        Example:
            await client.get_leverage_info(
                inst_id="BTC-USDT-SWAP",
                mgn_mode="cross"
            )
        """
        params: dict[str, Any] = {}
        if inst_id is not None:
            params["instId"] = join_iterable_field(inst_id)
        if ccy is not None:
            params["ccy"] = join_iterable_field(ccy)
        params["mgnMode"] = mgn_mode

        return await self.get(
            "/api/v5/account/leverage-info",
            params=params,
            auth=True,
        )

    async def set_leverage(
        self: HttpClientProtocol,
        leverage: int | str,
        mgn_mode: Literal["cross", "isolated"],
        inst_id: str | None = None,
        ccy: str | None = None,
        pos_side: Literal["long", "short"] | None = None,
    ) -> dict[str, Any]:
        """
        Set leverage with flexible parameters based on trade mode and instrument type.

        There are several scenarios for setting leverage.
        Depending on the margin mode, instrument type, and position mode,
        set leverage at the appropriate level:
          1. MARGIN/isolated at pairs (instId),
          2/4/5. MARGIN/cross at ccy,
          3. MARGIN/cross at pairs (instId)
          6. FUTURES/cross at contract (instId),
          7. FUTURES/isolated, buy/sell/contract level (instId)
          8. FUTURES/isolated, long/short/contract/posSide,
          9. SWAP/cross/contract,
          10. SWAP/isolated buy/sell/contract,
          11. SWAP/isolated/long-short/contract/posSide.

        Refer to OKX documentation for details:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-leverage

        Args:
            lever: Leverage to set (as integer or string, e.g. 5)
            mgn_mode: Margin mode, either "isolated" or "cross"
            inst_id: Instrument ID (e.g. "BTC-USDT-SWAP"),
                required for most cases except some "cross" margin cases
            ccy: Currency (e.g. "BTC"), required for some margin
                and spot cross-margin cases
            pos_side: Position side, "long" or "short".
                Required only for isolated, long/short mode for FUTURES/SWAP
                (see scenarios 8 and 11 in OKX doc)

        Returns:
            Dict containing the leverage result.

        Examples:
            1. Set leverage for MARGIN instruments under
                isolated-margin trade mode at pairs level.
            await client.set_leverage(lever=5, mgn_mode="isolated", inst_id="BTC-USDT")

            2. Set leverage for MARGIN/cross at currency level
            await client.set_leverage(lever=5, mgn_mode="cross", ccy="BTC")

            8. Set leverage for FUTURES/isolated/long-short/contract/posSide
            await client.set_leverage(
                lever=5,
                mgn_mode="isolated",
                inst_id="BTC-USDT-200802",
                pos_side="long",
            )

            11. Set leverage for SWAP/isolated/long-short/contract/posSide
            await client.set_leverage(
                lever=5,
                mgn_mode="isolated",
                inst_id="BTC-USDT-SWAP",
                pos_side="long",
            )
        """
        data: dict[str, Any] = {
            "lever": str(leverage),
            "mgnMode": mgn_mode,
        }
        if inst_id is not None:
            data["instId"] = inst_id
        if ccy is not None:
            data["ccy"] = ccy
        if pos_side is not None:
            data["posSide"] = pos_side

        return await self.post(
            "/api/v5/account/set-leverage",
            params=data,
            auth=True,
        )

    async def set_isolated_mode(
        self: HttpClientProtocol,
        iso_mode: Literal["auto_transfers_ccy", "automatic"],
        contracts_type: Literal["MARGIN", "CONTRACTS"],
    ) -> dict[str, Any]:
        """
        Set isolated margin trading settings.

        You can set the currency margin and futures/perpetual
        isolated margin trading mode.

        Rate Limit: 5 requests per 2 seconds
        Rate limit rule: User ID
        Permission: Trade

        See:
            https://www.okx.com/docs-v5/en/#trading-account-rest-api-set-isolated-mode

        HTTP Request:
            POST /api/v5/account/set-isolated-mode

        Args:
            iso_mode: Isolated margin trading setting.
                "auto_transfers_ccy": New auto transfers
                    (enables both base and quote currency
                    as the margin for isolated margin trading, only for MARGIN).
                "automatic": Auto transfers.
            contracts_type: Instrument type.
                "MARGIN" or "CONTRACTS".

        Returns:
            Dict containing the result of the mode setting.

        Example:
            await client.set_isolated_mode(iso_mode="automatic", type_="MARGIN")
        """
        data: dict[str, Any] = {
            "isoMode": iso_mode,
            "type": contracts_type,
        }
        return await self.post(
            "/api/v5/account/set-isolated-mode",
            params=data,
            auth=True,
        )
