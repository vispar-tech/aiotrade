from typing import Any, Dict

import orjson

from aiotrade._types import Exchange


class ExchangeResponseError(Exception):
    """Exception raised for errors returned by exchanges.

    Attributes:
        exchange (Exchange): The originating exchange ("bingx", "bybit", etc.).
        resp (dict): The full response dictionary from the exchange.
        message (str): The error message (human-readable).
        code (Any): Error code, if present.
    """

    def __init__(
        self,
        exchange: Exchange,
        resp: Dict[str, Any],
        message: str = "",
    ) -> None:
        self.resp = resp
        self.code = self._extract_code(resp)
        self.message = message or self._extract_message(resp)
        self.exchange: Exchange = exchange
        super().__init__(self.message)

    def __str__(self) -> str:
        parts = [f"ExchangeResponseError: {self.message}"]
        parts.append(f"Exchange: {self.exchange}")
        if self.code is not None:
            parts.append(f"Code: {self.code}")
        if self.resp:
            parts.append(f"Response: {self._format_response(self.resp)}")
        return "\n".join(parts)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(message={self.message!r}, code={self.code!r}, "
            f"resp={self.resp!r}, exchange={self.exchange!r})"
        )

    @staticmethod
    def _extract_message(resp: Dict[str, Any]) -> str:
        # Try to extract the typical error message fields.
        for key in ("msg", "message", "error", "retMsg", "error_message"):
            if key in resp and isinstance(resp[key], str):
                return str(resp[key])
        return "No error message found in response."

    @staticmethod
    def _extract_code(resp: Dict[str, Any]) -> Any:
        # Try to extract a typical error code field.
        for key in ("code", "retCode"):
            if key in resp:
                return resp[key]
        return None

    @staticmethod
    def _format_response(resp: Dict[str, Any]) -> str:
        try:
            return orjson.dumps(
                resp, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            ).decode("utf-8")
        except Exception:
            return str(resp)
