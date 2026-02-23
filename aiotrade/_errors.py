from typing import Any

import orjson

from aiotrade._types import Exchange

ResponseType = dict[str, Any] | list[dict[str, Any]]


class ExchangeResponseError(Exception):
    """Exception raised for errors returned by exchanges.

    Attributes:
        exchange (Exchange): The originating exchange ("bingx", "bybit", etc.).
        resp (dict or list[dict]): The full response from the exchange.
        message (str): The error message (human-readable).
        code (Any): Error code, if present.
    """

    def __init__(
        self,
        exchange: Exchange,
        resp: ResponseType,
        message: str = "",
    ) -> None:
        self.resp = resp
        self.code = self._extract_code(resp)
        self.message = message or self._extract_message(resp)
        self.exchange: Exchange = exchange
        super().__init__(self.message)

    def __str__(self) -> str:
        fields = [
            f"ExchangeResponseError: {self.message}",
            f"Exchange: {self.exchange}",
        ]
        if self.code is not None:
            fields.append(f"Code: {self.code}")
        if self.resp:
            fields.append(f"Response: {self._format_response(self.resp)}")
        return " ".join(fields)

    def __repr__(self) -> str:
        # Do not add \n in representation
        return (
            f"{self.__class__.__name__}"
            f"(message={self.message!r}, code={self.code!r}, "
            f"resp={self.resp!r}, exchange={self.exchange!r})"
        )

    @staticmethod
    def _extract_message(resp: ResponseType) -> str:
        # Support for dict or list[dict]
        if isinstance(resp, dict):
            for key in ("msg", "message", "error", "retMsg", "error_message"):
                if key in resp and isinstance(resp[key], str):
                    return str(resp[key])

        for entry in resp:
            if isinstance(entry, dict):
                for key in ("msg", "message", "error", "retMsg", "error_message"):
                    if key in entry and isinstance(entry[key], str):
                        return str(entry[key])
        return "No error message found in response."

    @staticmethod
    def _extract_code(resp: ResponseType) -> Any:
        # Support for dict or list[dict]
        if isinstance(resp, dict):
            for key in ("code", "retCode"):
                if key in resp:
                    return resp[key]
        for entry in resp:
            if isinstance(entry, dict):
                for key in ("code", "retCode"):
                    if key in entry:
                        return entry[key]
        return None

    @staticmethod
    def _format_response(resp: ResponseType) -> str:
        try:
            return orjson.dumps(
                resp, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            ).decode("utf-8")
        except Exception:
            return str(resp)
