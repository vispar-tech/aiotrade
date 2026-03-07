"""Tests for exchanges spot and swap account/portfolio balances."""

import asyncio
import json
import logging
import os
import sys
import time
import traceback
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv

from aiotrade import (
    BinanceClient,
    BingxClient,
    BitgetClient,
    BybitClient,
    ExchangeLiteral,
    ExchangeResponseError,
    OkxClient,
)
from aiotrade.types.bingx import PlaceSwapOrderParams
from aiotrade.types.bybit import PlaceOrderParams as BybitPlaceOrderParams
from aiotrade.types.bybit import SetTradingStopParams

load_dotenv()
PLACING_SYMBOL = "XRPUSDT"
PLACING_QTY = 100  # "QTY"
PLACING_LEVERAGE = 12
TAKE_PROFIT_PERCENT = 30
TRAILING_DELIVATION = 0.5
STOP_LOSS_PERCENT = 60

logging.basicConfig(stream=sys.stdout, level="CRITICAL")


def extract_symbol_asset(symbol: str) -> str:
    """
    Extracts the base asset from a trading symbol.

    E.g., 'BTCUSDT' -> 'BTC', 'ETH_USDT' -> 'ETH'.
    Removes any trailing '-' or '_' from the result.
    """
    quote_assets = ["-USDT", "USDT", "-USDC", "USDC", "-USDUSD"]
    for asset in quote_assets:
        pos = symbol.find(asset)
        if pos != -1:
            base = symbol[:pos]
            # Remove any trailing '-' or '_' before returning
            return base.rstrip("-_")
    # Fallback: handle symbols with an underscore, e.g. "BTC_USDT"
    base = symbol.split("_")[0] if "_" in symbol else symbol
    return base.rstrip("-_").lstrip()


def to_exchange_symbol(exchange: ExchangeLiteral, symbol: str) -> str:
    """Convert a symbol to the exchange-specific format."""
    asset = extract_symbol_asset(symbol)
    if exchange == "bingx":
        return asset + "-USDT"
    if exchange in ["bybit", "bitget", "binance"]:
        return asset + "USDT"
    if exchange == "okx":
        return asset + "-USDT-SWAP"
    raise NotImplementedError(f"Exchange {exchange} not implemented")


def _format_number(val: float | str) -> str:
    d = Decimal(str(val))
    return format(d, "f").rstrip("0").rstrip(".") if "." in format(d, "f") else str(d)


def check_env(required_vars: list[str]) -> tuple[bool, list[str]]:
    """Check presence of all given env vars."""
    values: list[str] = []
    missing: list[str] = []
    for var in required_vars:
        val = os.getenv(var)
        if val is None or val == "":
            missing.append(var)
        else:
            values.append(val)
    if missing:
        return False, missing
    return True, values


def get_tp_sl(price: float) -> tuple[float, float]:
    tp_tick = (TAKE_PROFIT_PERCENT / PLACING_LEVERAGE) / 100.0 * price
    # for long use plus
    raw_take_profit_price = price + tp_tick
    correct_take_profit_price = round(raw_take_profit_price, 4)
    # SL logic
    sl_tick = (STOP_LOSS_PERCENT / PLACING_LEVERAGE) / 100.0 * price
    # for long use minus
    raw_stop_loss_price = price - sl_tick
    correct_stop_loss_price = round(raw_stop_loss_price, 4)
    return correct_take_profit_price, correct_stop_loss_price


async def process_bingx(client: BingxClient) -> None:  # noqa: C901, PLR0912, PLR0915
    """Get BingX swap (futures) account balances: show entry for USDT."""
    print("await client.get_swap_account_balance()")
    print(json.dumps(await client.get_swap_account_balance(), indent=4))
    return

    async def get_open_orders() -> list[dict[str, Any]]:
        open_orders_response = await client.get_swap_open_orders(symbol=exchange_symbol)
        return [
            order
            for order in open_orders_response.get("data", {}).get("orders", [])
            if order["symbol"] == exchange_symbol
        ]

    async def get_open_position() -> dict[str, Any] | None:
        positions_response = await client.get_swap_positions(symbol=exchange_symbol)
        print("🟣 Current positions for", exchange_symbol, positions_response)
        return next(
            (
                p
                for p in positions_response.get("data", [])
                if p["symbol"] == exchange_symbol
            ),
            None,
        )

    try:
        exchange_symbol = to_exchange_symbol("bingx", PLACING_SYMBOL)
        print("Exchange symbol:", exchange_symbol)
        print("Will set leverage to", PLACING_LEVERAGE)
        # get balance
        result = await client.get_swap_account_balance()
        vst_entry = None
        for entry in result.get("data", []):
            if entry.get("asset") == "VST":
                vst_entry = entry
                break
        if not vst_entry:
            print("No VST swap asset found.")
            return

        available_balance = float(vst_entry["availableMargin"])
        print(
            "🟣 Available balance:",
            _format_number(available_balance),
        )

        current_position = await get_open_position()
        if current_position:
            print("‼️ Position already exist, canceling")
            position_id = current_position["positionId"]
            await client.close_swap_position(position_id=position_id)
            print("‼️ Position success closed")

        print(
            "🟣 Change margin to isolated:",
            await client.change_swap_margin_type(
                exchange_symbol, margin_type="ISOLATED"
            ),
        )

        print(
            "🟣 Leverage response:",
            await client.set_swap_leverage(exchange_symbol, "BOTH", PLACING_LEVERAGE),
        )

        klines_response = await client.get_swap_klines(
            symbol=exchange_symbol, interval="1m"
        )
        if (klines := klines_response.get("data", [])) and len(klines) > 1:
            last_kline_price = float(klines[-1]["close"])
            print(f"🟣 Last {PLACING_SYMBOL} price", last_kline_price)
            tp, sl = get_tp_sl(last_kline_price)
            print("🟣 TP/SL", tp, sl)
            print(
                "🟣 Placed orders response",
                await client.place_swap_batch_orders(
                    batch_orders=[
                        PlaceSwapOrderParams(
                            symbol=exchange_symbol,
                            side="BUY",
                            order_type="MARKET",
                            quantity=PLACING_QTY,
                            position_side="BOTH",
                        ),
                        PlaceSwapOrderParams(
                            symbol=exchange_symbol,
                            quantity=PLACING_QTY,
                            position_side="BOTH",
                            side="SELL",
                            order_type="TAKE_PROFIT_MARKET",
                            price=tp,
                            stop_price=tp,
                        ),
                        PlaceSwapOrderParams(
                            symbol=exchange_symbol,
                            quantity=PLACING_QTY,
                            position_side="BOTH",
                            side="SELL",
                            order_type="STOP_MARKET",
                            price=sl,
                            stop_price=sl,
                        ),
                    ]
                ),
            )

            print("🟣 Waiting 2 seconds")
            time.sleep(2)
            current_position = await get_open_position()
            if current_position:
                position_id = current_position["positionId"]

                open_orders = await get_open_orders()
                tp_order = next(
                    (
                        order
                        for order in open_orders
                        if order["type"] == "TAKE_PROFIT_MARKET"
                    ),
                    None,
                )
                sl_order = next(
                    (order for order in open_orders if order["type"] == "STOP_MARKET"),
                    None,
                )

                print("🟣 Take profit order for", exchange_symbol, tp_order)
                print("🟣 Stop loss order for", exchange_symbol, sl_order)

                if tp_order is None:
                    print("‼️ TP Order not found after placing")
                    raise Exception("TP Order not found after placing")
                if sl_order is None:
                    print("‼️ SL Order not found after placing")
                    raise Exception("SL Order not found after placing")

                print("🟣 Waiting 2 seconds")
                time.sleep(2)

                print(
                    "🟣 Cancel TP order",
                    await client.cancel_swap_batch_orders(
                        symbol=exchange_symbol, order_id_list=[tp_order["orderId"]]
                    ),
                )

                open_orders = await get_open_orders()
                tp_order = next(
                    (
                        order
                        for order in open_orders
                        if order["type"] == "TAKE_PROFIT_MARKET"
                    ),
                    None,
                )
                sl_order = next(
                    (order for order in open_orders if order["type"] == "STOP_MARKET"),
                    None,
                )
                if tp_order is not None:
                    print("‼️ TP Order already exist after cancel")
                    raise Exception("TP Order already exist after cancel")
                if sl_order is None:
                    print("‼️ SL Order not found after cancel TP")
                    raise Exception("SL Order not found after cancel TP")

                print(
                    "🟣 Place trailing take profit response",
                    await client.place_swap_batch_orders(
                        batch_orders=[
                            PlaceSwapOrderParams(
                                symbol=exchange_symbol,
                                quantity=PLACING_QTY,
                                position_side="BOTH",
                                side="SELL",
                                order_type="TRAILING_TP_SL",
                                # NOTE: For bingx as percent value
                                price_rate=TRAILING_DELIVATION / 100,
                                activation_price=tp,
                            ),
                        ]
                    ),
                )

                print("🟣 Waiting 2 seconds")
                time.sleep(2)

                open_orders = await get_open_orders()
                trailing_order = next(
                    (
                        order
                        for order in open_orders
                        if order["type"] == "TRAILING_TP_SL"
                    ),
                    None,
                )
                sl_order = next(
                    (order for order in open_orders if order["type"] == "STOP_MARKET"),
                    None,
                )
                if trailing_order is None:
                    print("‼️ Trailing Order not found after placing")
                    raise Exception("Trailing Order not found after placing")
                if sl_order is None:
                    print("‼️ SL Order not found after placing trailing")
                    raise Exception("SL Order not found after placing trailing")

                print("🟣 Trailing profit order for", exchange_symbol, trailing_order)

                print("🟣 Closing position")
                await client.close_swap_position(position_id=position_id)
                print("🟣 Position success closed")

                print("✅ BingX successfully pass basic placement")

    except Exception as e:
        print(f"❌ Error process bingx: {e}")
        traceback.print_exc()


async def process_bybit(client: BybitClient) -> None:  # noqa: C901, PLR0912, PLR0915
    """Get Bybit unified (futures) wallet balance: show entry for USDT."""
    print("await client.get_wallet_balance()")
    print(json.dumps(await client.get_wallet_balance(), indent=4))

    return

    async def get_open_orders() -> list[dict[str, Any]]:
        open_orders_response = await client.get_open_and_closed_orders(
            category="linear", symbol=exchange_symbol, settle_coin="USDT"
        )
        return [
            order
            for order in open_orders_response.get("result", {}).get("list", [])
            if order["symbol"] == exchange_symbol
        ]

    async def get_open_position() -> dict[str, Any] | None:
        positions_response = await client.get_position_info(
            category="linear", symbol=exchange_symbol, settle_coin="USDT"
        )
        print("🟣 Current positions for", exchange_symbol, positions_response)
        return next(
            (
                p
                for p in positions_response.get("result", {}).get("list", [])
                if p["symbol"] == exchange_symbol and p["avgPrice"] != "0"
            ),
            None,
        )

    try:
        exchange_symbol = to_exchange_symbol("bybit", PLACING_SYMBOL)
        print("Exchange symbol:", exchange_symbol)
        print("Will set leverage to", PLACING_LEVERAGE)
        # get balance
        result = await client.get_wallet_balance(account_type="UNIFIED")
        usdt_entry = None
        for account in result.get("result", {}).get("list", []):
            for coin in account.get("coin", []):
                if coin.get("coin") == "USDT":
                    usdt_entry = coin
                    break
            if usdt_entry:
                break
        if not usdt_entry:
            print("No USDT asset found.")
            return

        available_balance = (
            float(usdt_entry.get("walletBalance") or 0)
            - float(usdt_entry.get("totalPositionIM") or 0)
            + float(usdt_entry.get("unrealisedPnl") or 0)
        )
        print(
            "🟡 Available balance:",
            _format_number(available_balance),
        )

        current_position = await get_open_position()
        if current_position:
            print("‼️ Position already exist, canceling")
            await client.place_order(
                category="linear",
                params=BybitPlaceOrderParams(
                    symbol=exchange_symbol,
                    side="Sell" if current_position["side"] == "Buy" else "Buy",
                    order_type="Market",
                    qty=current_position["size"],
                    reduce_only=True,
                ),
            )
            print("‼️ Position success closed")

        try:
            lev_response = await client.set_leverage(
                "linear", exchange_symbol, PLACING_LEVERAGE, PLACING_LEVERAGE
            )
            print("🟡 Leverage response", lev_response)
        except ExchangeResponseError as err:
            if err.code != 110043:
                raise
            print(
                "🟡 Leverage response [leverage not modified]",
            )
        except Exception as exc:
            print(f"❌ Error setting leverage: {exc}")

        klines_response = await client.get_kline(
            category="linear", symbol=exchange_symbol, interval="1"
        )
        if (klines := klines_response.get("result", {}).get("list", [])) and len(
            klines
        ) > 1:
            last_kline_price = float(klines[-1][4])
            print(f"🟡 Last {PLACING_SYMBOL} price", last_kline_price)
            tp, sl = get_tp_sl(last_kline_price)
            trailing_delivation_value = abs(tp - tp - (tp * TRAILING_DELIVATION / 100))
            print("🟡 TP/SL", tp, sl)
            print(
                "🟡 Placed orders response",
                await client.batch_place_order(
                    category="linear",
                    orders=[
                        BybitPlaceOrderParams(
                            symbol=exchange_symbol,
                            side="Buy",
                            order_type="Market",
                            qty=PLACING_QTY,
                        ),
                    ],
                ),
            )

            print("🟡 Waiting 2 seconds")
            time.sleep(2)
            current_position = await get_open_position()
            if current_position:
                # set trading stop
                await client.set_trading_stop(
                    category="linear",
                    params=SetTradingStopParams(
                        symbol=exchange_symbol,
                        position_idx=0,
                        tpsl_mode="Full",
                        take_profit=tp,
                        stop_loss=sl,
                    ),
                )
                open_orders = await get_open_orders()
                tp_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "TakeProfit"
                    ),
                    None,
                )
                sl_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "StopLoss"
                    ),
                    None,
                )

                print("🟡 Take profit order for", exchange_symbol, tp_order)
                print("🟡 Stop loss order for", exchange_symbol, sl_order)

                if tp_order is None:
                    print("‼️ TP Order not found after placing")
                    raise Exception("TP Order not found after placing")
                if sl_order is None:
                    print("‼️ SL Order not found after placing")
                    raise Exception("SL Order not found after placing")

                print("🟡 Waiting 2 seconds")
                time.sleep(2)

                print(
                    "🟡 Cancel TP",
                    await client.set_trading_stop(
                        category="linear",
                        params=SetTradingStopParams(
                            symbol=exchange_symbol,
                            position_idx=0,
                            tpsl_mode="Full",
                            take_profit=0,
                            stop_loss=sl,
                        ),
                    ),
                )

                open_orders = await get_open_orders()
                tp_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "TakeProfit"
                    ),
                    None,
                )
                sl_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "StopLoss"
                    ),
                    None,
                )
                if tp_order is not None:
                    print("‼️ TP Order already exist after cancel")
                    raise Exception("TP Order already exist after cancel")
                if sl_order is None:
                    print("‼️ SL Order not found after cancel TP")
                    raise Exception("SL Order not found after cancel TP")

                print(
                    "🟡 Place trailing take profit response",
                    await client.set_trading_stop(
                        category="linear",
                        params=SetTradingStopParams(
                            symbol=exchange_symbol,
                            position_idx=0,
                            tpsl_mode="Full",
                            # NOTE: For bybit as percent of price
                            trailing_stop=trailing_delivation_value,
                            active_price=tp,
                        ),
                    ),
                )

                print("🟡 Waiting 2 seconds")
                time.sleep(2)

                open_orders = await get_open_orders()

                trailing_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "TrailingProfit"
                    ),
                    None,
                )
                sl_order = next(
                    (
                        order
                        for order in open_orders
                        if order["orderType"] == "Market"
                        and order["stopOrderType"] == "StopLoss"
                    ),
                    None,
                )
                if trailing_order is None:
                    print("‼️ Trailing Order not found after placing")
                    raise Exception("Trailing Order not found after placing")
                if sl_order is None:
                    print("‼️ SL Order not found after placing trailing")
                    raise Exception("SL Order not found after placing trailing")

                print("🟡 Trailing profit order for", exchange_symbol, trailing_order)

                print("🟡 Closing position")
                await client.place_order(
                    category="linear",
                    params=BybitPlaceOrderParams(
                        symbol=exchange_symbol,
                        side="Sell",
                        order_type="Market",
                        qty=PLACING_QTY,
                        reduce_only=True,
                    ),
                )
                print("🟡 Position success closed")
                current_position = await get_open_position()
                if current_position is not None:
                    print("‼️ Position exists after cancel")
                    raise Exception("Position exists after cancel")

                print("✅ Bybit successfully pass basic placement")

    except Exception as e:
        print(f"❌ Error process Bybit: {e}")


async def process_okx(client: OkxClient) -> None:
    """Get OKX wallet (futures/etc) balances: show entry for USDT."""
    print(await client.get_leverage_info(mgn_mode="cross", inst_id="BTC-USDT-SWAP"))
    print(await client.set_leverage(20, "isolated", inst_id="BTC-USDT-SWAP"))
    # print(await client.get_account_config())
    # print("await await client.get_instruments(inst_type='SWAP')")
    # print(
    #     json.dumps(
    #         await client.get_instruments(inst_type="SWAP", inst_id="BTC-USDT-SWAP"),
    #         indent=2,
    #     )
    # )
    return
    print("await client.get_positions(inst_type='SWAP')")
    print(json.dumps(await client.get_positions(inst_type="SWAP"), indent=4))
    # Calculate start_time: 7 days ago (UTC timestamp in ms)
    start_from_dt = datetime.now(UTC) - timedelta(days=7)
    start_from_timestamp = int(start_from_dt.timestamp() * 1000)

    total_pnls: list[dict[str, Any]] = []
    after_cursor: int | None = start_from_timestamp
    req_limit = 100

    while True:
        try:
            # Call /api/v5/account/positions-history with paginated `after`
            result = await client.get_positions_history(
                inst_type="SWAP",  # Note: API parameter is 'instType'
                after=after_cursor,  # Paginate using last seen uTime
                limit=req_limit,  # Okx expects string for limit
            )
            # API returns a top-level 'data': [ ...list of positions... ]
            positions: list[dict[str, Any]] = result.get("data", [])
        except Exception as exc:
            print(f"OKX positions-history fetch error: {exc!s}")
            break

        if not positions:
            break

        total_pnls.extend(positions)

        # Find max uTime to paginate to next
        u_times = [int(pos.get("uTime", "0")) for pos in positions if "uTime" in pos]
        if u_times:
            max_u_time = max(u_times)
            # Advance `after_cursor` for next page
            after_cursor = int(max_u_time)
            # If we've reached the maximum time covered by the response, break the loop
            if len(positions) < req_limit:
                break
        else:
            break

    print(f"Loaded {len(total_pnls)} OKX PNL history rows in last 7 days.")
    print(json.dumps(total_pnls, indent=2))
    return

    async def get_open_orders() -> list[dict[str, Any]]:
        open_orders_response = await client.get_orders_pending(
            inst_type="SWAP", state="live"
        )
        return [
            order
            for order in open_orders_response.get("data", [])
            if order["instId"] == exchange_symbol
        ]

    async def get_algo_open_orders() -> list[dict[str, Any]]:
        algo_orders_reponse = await client.get_algo_orders_pending(
            ord_type="conditional",
            inst_type="SWAP",
        )
        return [
            order
            for order in algo_orders_reponse.get("data", [])
            if order["instId"] == exchange_symbol
        ]

    async def get_open_position() -> dict[str, Any] | None:
        positions_response = await client.get_positions(
            inst_type="SWAP", inst_id=exchange_symbol
        )
        print("🟣 Current positions for", exchange_symbol, positions_response)
        return next(
            (
                p
                for p in positions_response.get("data", [])
                if p["instId"] == exchange_symbol
            ),
            None,
        )

    try:
        exchange_symbol = to_exchange_symbol("okx", PLACING_SYMBOL)
        print("Exchange symbol:", exchange_symbol)
        print("Will set leverage to", PLACING_LEVERAGE)
        # get balance
        result = await client.get_balance()
        usdt_detail = None
        for account in result.get("data", []):
            for detail in account.get("details", []):
                if detail.get("ccy") == "USDT":
                    usdt_detail = detail
                    break
            if usdt_detail:
                break
        if not usdt_detail:
            print("No USDT asset found.")
            return

        available_balance = float(usdt_detail["availBal"])
        print(
            "🟢 Available balance:",
            _format_number(available_balance),
        )

        print(
            "🟢 Leverage response",
            await client.set_leverage(PLACING_LEVERAGE, "isolated", exchange_symbol),
        )

        print(
            await get_algo_open_orders(),
            await get_open_orders(),
            await get_open_position(),
        )

    except Exception as e:
        print(f"❌ Error process OKX: {e}")


async def process_bitget(client: BitgetClient) -> None:
    """Get Bitget futures/swap wallet balances: show entry for USDT."""
    # print("await client.get_contract_config('USDT-FUTURES')")
    # print(
    #     json.dumps(
    #         await client.get_contract_config("USDT-FUTURES", symbol="BTCUSDT"), indent=4
    #     )
    # )
    await client.set_position_mode(product_type="USDT-FUTURES", pos_mode="one_way_mode")
    print(
        json.dumps(
            await client.get_single_account(
                symbol="BTCUSDT",
                product_type="USDT-FUTURES",
                margin_coin="USDT",
            ),
            indent=4,
        )
    )
    return
    try:
        exchange_symbol = to_exchange_symbol("bitget", PLACING_SYMBOL)
        print("Exchange symbol:", exchange_symbol)
        print("Will set leverage to", PLACING_LEVERAGE)
        # get balance
        result = await client.get_account_list("USDT-FUTURES")
        usdt_account = None
        for account in result.get("data", []):
            if account.get("marginCoin") == "USDT":
                usdt_account = account
                break
        if not usdt_account:
            print("No USDT asset found.")
            return

        available_balance = float(usdt_account["available"])
        print(
            "🔴 Available balance:",
            _format_number(available_balance),
        )
        print(
            "🔴 Leverage response",
            await client.set_leverage(
                exchange_symbol,
                "USDT-FUTURES",
                "USDT",
                leverage=str(PLACING_LEVERAGE),
            ),
        )

    except Exception as e:
        print(f"❌ Error process Bitget: {e}")


async def process_binance(client: BinanceClient) -> None:
    """Get Binance USD-M Futures account balances: show entry for USDT."""
    print("await client.get_exchange_info()")
    exchange_info = await client.get_exchange_info()
    symbols = exchange_info.get("result", {}).get("symbols", [])
    btcusdt_info = next((s for s in symbols if s.get("symbol") == "BTCUSDT"), None)
    print(json.dumps(btcusdt_info, indent=4))

    return
    print("await client.get_position_info()")
    # await client.change_position_mode(dual_side_position=True)
    print(json.dumps(await client.get_position_info(), indent=4))

    # Calculate start_time: 7 days ago (UTC timestamp in ms)
    start_from_dt = datetime.now(UTC) - timedelta(days=7)
    start_from_timestamp = int(start_from_dt.timestamp() * 1000)

    total_pnls: list[dict[str, Any]] = []
    req_limit = 1000
    page = 1

    while True:
        try:
            # Call get_income_history for "REALIZED_PNL", paginating by page
            result = await client.get_income_history(
                income_type="REALIZED_PNL",
                start_time=start_from_timestamp,
                page=page,
                limit=req_limit,
            )
            # Some Binance APIs may use 'rows', 'data', or similar - this may be specific to your implementation
            # Replace 'rows' with the correct key if needed
            positions: list[dict[str, Any]] = result.get("result", {}).get("list", [])
        except Exception as exc:
            print(f"Binance income-history fetch error: {exc!s}")
            break

        if not positions:
            break

        total_pnls.extend(positions)

        if len(positions) < req_limit:
            break  # Last page reached

        page += 1  # Move to next page

    print(f"Loaded {len(total_pnls)} Binance PNL history rows in last 7 days.")
    print(json.dumps(total_pnls, indent=2))

    return
    try:
        exchange_symbol = to_exchange_symbol("binance", PLACING_SYMBOL)
        print("Exchange symbol:", exchange_symbol)
        print("Will set leverage to", PLACING_LEVERAGE)
        # get balance
        result = await client.get_account_balance()
        usdt_entry = None
        for entry in result.get("result", {}).get("list", []):
            if (
                entry.get("asset") == "USDT"
                and float(entry.get("availableBalance", 0)) != 0
            ):
                usdt_entry = entry
                break
        if not usdt_entry:
            print("No USDT futures asset found.")
            return

        available_balance = float(usdt_entry["availableBalance"])
        print(
            "🟠 Available balance:",
            _format_number(available_balance),
        )

        print(
            "🟠 Leverage response",
            await client.change_leverage(exchange_symbol, PLACING_LEVERAGE),
        )
    except Exception as e:
        print(f"❌ Error retrieving Binance futures account balances: {e}")


async def main() -> None:  # noqa: PLR0912, PLR0915
    # Load enabled flags for each exchange
    bingx_enabled = os.getenv("BINGX_ENABLED", "false").lower() == "true"
    bybit_enabled = os.getenv("BYBIT_ENABLED", "false").lower() == "true"
    okx_enabled = os.getenv("OKX_ENABLED", "false").lower() == "true"
    bitget_enabled = os.getenv("BITGET_ENABLED", "false").lower() == "true"
    binance_enabled = os.getenv("BINANCE_ENABLED", "false").lower() == "true"

    # Process BingX
    bingx_ok, bingx_values = check_env(["BINGX_API_KEY", "BINGX_API_SECRET"])
    print("==================== BingX ====================")
    if bingx_enabled and bingx_ok:
        bingx_api_key, bingx_api_secret = bingx_values
        bingx_client = BingxClient(
            api_key=bingx_api_key, api_secret=bingx_api_secret, demo=True
        )
        await process_bingx(bingx_client)
        await bingx_client.close()
    elif not bingx_enabled:
        print("❌ Skipping BingX test. Disabled via BINGX_ENABLED env var.")
    else:
        missing = ", ".join(bingx_values)
        print(f"❌ Skipping BingX test. Missing env vars: {missing}")

    # Process Bybit (use BYBIT_DEMO_API_KEY / BYBIT_DEMO_API_SECRET)
    bybit_ok, bybit_values = check_env(["BYBIT_API_KEY", "BYBIT_API_SECRET"])
    print("\n==================== Bybit ====================")
    if bybit_enabled and bybit_ok:
        bybit_api_key, bybit_api_secret = bybit_values
        bybit_client = BybitClient(
            api_key=bybit_api_key, api_secret=bybit_api_secret, demo=True, testnet=False
        )
        await process_bybit(bybit_client)
        await bybit_client.close()
    elif not bybit_enabled:
        print("❌ Skipping Bybit test. Disabled via BYBIT_ENABLED env var.")
    else:
        missing = ", ".join(bybit_values)
        print(f"❌ Skipping Bybit test. Missing env vars: {missing}")

    # Process OKX
    okx_ok, okx_values = check_env(
        ["OKX_API_KEY", "OKX_API_SECRET", "OKX_API_PASSPHRASE"]
    )
    print("\n==================== OKX ====================")
    if okx_enabled and okx_ok:
        okx_api_key, okx_api_secret, okx_passphrase = okx_values
        okx_client = OkxClient(
            api_key=okx_api_key,
            api_secret=okx_api_secret,
            passphrase=okx_passphrase,
            demo=True,
        )
        await process_okx(okx_client)
        await okx_client.close()
    elif not okx_enabled:
        print("❌ Skipping OKX test. Disabled via OKX_ENABLED env var.")
    else:
        missing = ", ".join(okx_values)
        print(f"❌ Skipping OKX test. Missing env vars: {missing}")

    # Process Bitget
    bitget_ok, bitget_values = check_env(
        ["BITGET_API_KEY", "BITGET_API_SECRET", "BITGET_API_PASSPHRASE"]
    )
    print("\n==================== Bitget ====================")
    if bitget_enabled and bitget_ok:
        bitget_api_key, bitget_api_secret, bitget_passphrase = bitget_values
        bitget_client = BitgetClient(
            api_key=bitget_api_key,
            api_secret=bitget_api_secret,
            passphrase=bitget_passphrase,
            demo=True,
        )
        await process_bitget(bitget_client)
        await bitget_client.close()
    elif not bitget_enabled:
        print("❌ Skipping Bitget test. Disabled via BITGET_ENABLED env var.")
    else:
        missing = ", ".join(bitget_values)
        print(f"❌ Skipping Bitget test. Missing env vars: {missing}")

    # Process Binance
    binance_ok, binance_values = check_env(["BINANCE_API_KEY", "BINANCE_API_SECRET"])
    print("\n==================== Binance ====================")
    if binance_enabled and binance_ok:
        binance_api_key, binance_api_secret = binance_values
        binance_client = BinanceClient(
            api_key=binance_api_key, api_secret=binance_api_secret, demo=True
        )
        await process_binance(binance_client)
        await binance_client.close()
    elif not binance_enabled:
        print("❌ Skipping Binance test. Disabled via BINANCE_ENABLED env var.")
    else:
        missing = ", ".join(binance_values)
        print(f"❌ Skipping Binance test. Missing env vars: {missing}")


if __name__ == "__main__":
    asyncio.run(main())
