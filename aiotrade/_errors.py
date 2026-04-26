from typing import Any

import orjson

from aiotrade._types import Exchange


class ExchangeResponseError(Exception):
    """
    Exception for exchange error responses.

    Args:
        exchange: Exchange identifier (e.g. "binance").
        resp: Full response returned by the exchange (dict).
        message: Custom human-readable error message (optional).

    Attributes:
        exchange: Originating exchange.
        resp: The original response.
        message: Error message (best human-readable extraction or passed-in text).
        code: Error code if found, otherwise None.
    """

    _MESSAGE_KEYS = ("msg", "message", "error", "retMsg", "error_message")
    _CODE_KEYS = ("code", "retCode")

    def __init__(
        self, exchange: Exchange, resp: dict[str, Any], message: str = ""
    ) -> None:
        self.exchange: Exchange = exchange
        self.resp: dict[str, Any] = resp
        self.code: Any = self._extract_code(resp)
        self.message: str = message or self._extract_message(resp)
        super().__init__(self.message)

    def __str__(self) -> str:
        # Log-like one-line format, no newlines
        parts = [
            f"ExchangeResponseError at request to {self.exchange}",
            f"message={self.message}",
        ]
        if self.code is not None:
            parts.append(f"code={self.code}")
        if self.resp:
            parts.append(f"response={self._format_response(self.resp)}")
        return ", ".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"exchange={self.exchange!r}, message={self.message!r}, "
            f"code={self.code!r}, resp={self.resp!r})"
        )

    @classmethod
    def _extract_message(cls, resp: dict[str, Any]) -> str:
        for key in cls._MESSAGE_KEYS:
            val = resp.get(key)
            if isinstance(val, str):
                return val
        return "No error message found in response."

    @classmethod
    def _extract_code(cls, resp: dict[str, Any]) -> Any:
        for key in cls._CODE_KEYS:
            if key in resp:
                return resp[key]
        return None

    @staticmethod
    def _format_response(resp: dict[str, Any]) -> str:
        # Compact single-line JSON string
        try:
            return orjson.dumps(resp, option=orjson.OPT_SORT_KEYS).decode("utf-8")
        except Exception:
            return str(resp)
