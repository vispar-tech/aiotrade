from typing import Any

import orjson

from aiotrade._types import Exchange

ResponseType = dict[str, Any] | list[dict[str, Any]]


class ExchangeResponseError(Exception):
    """
    Exception for exchange error responses.

    Args:
        exchange: Exchange identifier (e.g. "binance").
        resp: Full response returned by the exchange (dict or list of dicts).
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
        self, exchange: Exchange, resp: ResponseType, message: str = ""
    ) -> None:
        self.exchange: Exchange = exchange
        self.resp: ResponseType = resp
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
    def _extract_message(cls, resp: ResponseType) -> str:
        if isinstance(resp, dict):
            for key in cls._MESSAGE_KEYS:
                val = resp.get(key)
                if isinstance(val, str):
                    return val
        for entry in resp:
            if isinstance(entry, dict):
                for key in cls._MESSAGE_KEYS:
                    val = entry.get(key)
                    if isinstance(val, str):
                        return val
        return "No error message found in response."

    @classmethod
    def _extract_code(cls, resp: ResponseType) -> Any:
        if isinstance(resp, dict):
            for key in cls._CODE_KEYS:
                if key in resp:
                    return resp[key]
        for entry in resp:
            if isinstance(entry, dict):
                for key in cls._CODE_KEYS:
                    if key in entry:
                        return entry[key]
        return None

    @staticmethod
    def _format_response(resp: ResponseType) -> str:
        # Compact single-line JSON string
        try:
            return orjson.dumps(resp, option=orjson.OPT_SORT_KEYS).decode("utf-8")
        except Exception:
            return str(resp)
