from typing import Any, Dict

import orjson


class ExchangeResponseError(Exception):
    """Exception raised for errors returned by exchanges.

    Attributes:
        resp (dict): The full response dictionary from the exchange.
        message (str): The error message (human-readable).
    """

    def __init__(self, resp: Dict[str, Any], message: str = "") -> None:
        self.resp = resp
        self.message = message or self._extract_message(resp)
        super().__init__(self.message)

    def __str__(self) -> str:
        details = f"ExchangeResponseError: {self.message}"
        if self.resp:
            details += f"\nResponse: {self._format_response(self.resp)}"
        return details

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(message={self.message!r}, resp={self.resp!r})"
        )

    @staticmethod
    def _extract_message(resp: Dict[str, Any]) -> str:
        # Try to extract the typical error message fields.
        for key in ("msg", "message", "error", "retMsg", "error_message"):
            if key in resp and isinstance(resp[key], str):
                return str(resp[key])
        return "No error message found in response."

    @staticmethod
    def _format_response(resp: Dict[str, Any]) -> str:
        try:
            return orjson.dumps(
                resp, option=orjson.OPT_INDENT_2 | orjson.OPT_SORT_KEYS
            ).decode("utf-8")
        except Exception:
            return str(resp)
