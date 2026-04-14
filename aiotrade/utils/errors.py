"""Exchange error handling and masking utilities."""

import logging
import re
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, NamedTuple

from aiohttp import ClientResponseError

from aiotrade import ExchangeResponseError

BINGX_UNBLOCK_REGEX = r"unblocked after (\d+)"
BINGX_API_KEY_BAN_MINUTES = 5
BYBIT_API_KEY_BAN_MINUTES = 5
BINANCE_RATE_LIMIT_BAN_MINUTES = 1

_SENSITIVE_HEADERS = {
    "OK-ACCESS-KEY",
    "OK-ACCESS-SIGN",
    "OK-ACCESS-PASSPHRASE",
    "KC-API-KEY",
    "KC-API-SIGN",
    "KC-API-PASSPHRASE",
    "KC-API-PARTNER-SIGN",
    "X-BAPI-API-KEY",
    "X-BAPI-SIGN",
    "ACCESS-KEY",
    "ACCESS-SIGN",
    "ACCESS-PASSPHRASE",
    "X-BX-APIKEY",
    "X-MBX-APIKEY",
}


def _mask_headers(headers: dict[str, Any]) -> dict[str, Any]:
    masked: dict[str, Any] = {}
    for k, v in headers.items():
        if k.upper() in _SENSITIVE_HEADERS:
            if isinstance(v, str):
                masked[k] = v[:6] + "..."
            else:
                masked[k] = "****"
        else:
            masked[k] = v
    return masked


def _mask_signature(url: str) -> str:
    """Mask the signature or sign value in a crypto API URL's query string."""
    for sig_key in ["signature=", "sign="]:
        i = url.find(sig_key)
        if i != -1:
            amp = url.find("&", i)
            if amp == -1:
                return url[: i + len(sig_key)] + "***"
            return url[: i + len(sig_key)] + "***" + url[amp:]
    return url


class ExchangeErrorCategory(Enum):
    """Categories of typical errors when handling responses from crypto exchanges."""

    UNKNOWN = auto()
    RATE_LIMIT = auto()
    RATE_LIMIT_WITH_BAN = auto()
    RETRY_LATER = auto()
    TEMP_UNAVAILABLE = auto()
    BAD_REQUEST = auto()
    API_KEY_EXPIRED = auto()


class ExchangeErrorAnalysis(NamedTuple):
    """
    Structured output describing a crypto exchange error analysis.

    Attributes:
        category: Category for the error type.
        ban_until: Optional timestamp (milliseconds) to
            which the ban/rate-limit applies.
        message: Optional human-readable message associated with the error.
    """

    category: ExchangeErrorCategory
    ban_until: int | None = None  # ms timestamp if applicable
    message: str | None = None


class HttpErrorCategory(Enum):
    """Categories for typical HTTP error codes."""

    UNKNOWN = auto()
    BAD_REQUEST = auto()
    UNAUTHORIZED = auto()
    FORBIDDEN = auto()
    RATE_LIMITED = auto()
    SERVER_ERROR = auto()
    SERVICE_UNAVAILABLE = auto()
    RETRY_LATER = auto()


class HttpErrorAnalysis(NamedTuple):
    """
    Structured output describing a HTTP error analysis.

    Attributes:
        category: Category for the HTTP error type.
        message: Human-readable message, if available.
        status: HTTP status code.
        url: Relevant URL for the error context.
        method: HTTP method.
        headers: HTTP response headers (masked).
    """

    category: HttpErrorCategory
    message: str | None = None
    status: int | None = None
    url: str | None = None
    method: str | None = None
    headers: dict[str, Any] | None = None


def _log_http_error(
    display_name: str | None,
    log_prefix: str,
    category: HttpErrorCategory,
    log_msg: str,
    message: str,
    headers_dict: dict[str, Any] | None,
    log_func: Callable[..., None],
) -> None:
    if display_name is not None:
        log_func(
            "%s %s error category=%s msg=%s (body=%s, headers=%s)",
            display_name,
            log_prefix,
            category.name,
            log_msg,
            message,
            headers_dict,
        )
    else:
        log_func(
            "%s error category=%s msg=%s (body=%s, headers=%s)",
            log_prefix,
            category.name,
            log_msg,
            message,
            headers_dict,
        )


def analyze_http_client_response_error(  # noqa: PLR0911
    e: ClientResponseError,
    display_name: str | None,
    logger: logging.Logger,
) -> HttpErrorAnalysis:
    """
    Analyze aiohttp.ClientResponseError, categorize, and log in a structured way.

    Args:
        e: The ClientResponseError instance.
        logger: Logger instance for tracing.

    Returns:
        HttpErrorAnalysis with assigned category and description.
    """
    status = e.status
    url_str = ""
    method = None

    # Best effort to extract request info and mask sensitive bits
    url_str = str(e.request_info.real_url)
    url_str = _mask_signature(url_str)
    method = e.request_info.method

    message = e.message or str(e)
    headers_dict: dict[str, Any] | None = None
    if e.headers is not None:
        try:
            headers_dict = _mask_headers(dict(e.headers))
        except Exception:
            headers_dict = None

    log_prefix = f"[HTTP {status}] {method or ''} {url_str}".strip()

    # 4xx: Client errors
    if 400 <= status < 500:
        if status == 401:
            _log_http_error(
                display_name,
                log_prefix,
                HttpErrorCategory.UNAUTHORIZED,
                "Unauthorized (401). Verify authentication/API key.",
                message,
                headers_dict,
                logger.warning,
            )
            return HttpErrorAnalysis(
                category=HttpErrorCategory.UNAUTHORIZED,
                message=message or "HTTP 401 Unauthorized",
                status=status,
                url=url_str,
                method=method,
                headers=headers_dict,
            )
        if status == 403:
            _log_http_error(
                display_name,
                log_prefix,
                HttpErrorCategory.FORBIDDEN,
                "Forbidden (403). API key/permissions issue.",
                message,
                headers_dict,
                logger.error,  # 403 is a significant access-control error
            )
            return HttpErrorAnalysis(
                category=HttpErrorCategory.FORBIDDEN,
                message=message or "HTTP 403 Forbidden",
                status=status,
                url=url_str,
                method=method,
                headers=headers_dict,
            )
        if status == 429:
            _log_http_error(
                display_name,
                log_prefix,
                HttpErrorCategory.RATE_LIMITED,
                "Rate limit reached (429).",
                message,
                headers_dict,
                logger.warning,
            )
            return HttpErrorAnalysis(
                category=HttpErrorCategory.RATE_LIMITED,
                message=message or "HTTP 429 Too Many Requests",
                status=status,
                url=url_str,
                method=method,
                headers=headers_dict,
            )
        _log_http_error(
            display_name,
            log_prefix,
            HttpErrorCategory.BAD_REQUEST,
            f"HTTP client error {status}.",
            message,
            headers_dict,
            logger.warning,
        )
        return HttpErrorAnalysis(
            category=HttpErrorCategory.BAD_REQUEST,
            message=message or f"HTTP {status} Client Error",
            status=status,
            url=url_str,
            method=method,
            headers=headers_dict,
        )
    # 5xx: Server errors
    if 500 <= status < 600:
        if status == 503:
            _log_http_error(
                display_name,
                log_prefix,
                HttpErrorCategory.SERVICE_UNAVAILABLE,
                "Service unavailable (503).",
                message,
                headers_dict,
                logger.warning,
            )
            return HttpErrorAnalysis(
                category=HttpErrorCategory.SERVICE_UNAVAILABLE,
                message=message or "HTTP 503 Service Unavailable",
                status=status,
                url=url_str,
                method=method,
                headers=headers_dict,
            )
        if status == 504:
            _log_http_error(
                display_name,
                log_prefix,
                HttpErrorCategory.RETRY_LATER,
                "Gateway timeout (504). Retry possible.",
                message,
                headers_dict,
                logger.warning,
            )
            return HttpErrorAnalysis(
                category=HttpErrorCategory.RETRY_LATER,
                message=message or "HTTP 504 Gateway Timeout",
                status=status,
                url=url_str,
                method=method,
                headers=headers_dict,
            )
        _log_http_error(
            display_name,
            log_prefix,
            HttpErrorCategory.SERVER_ERROR,
            f"HTTP server error {status}.",
            message,
            headers_dict,
            logger.warning,
        )
        return HttpErrorAnalysis(
            category=HttpErrorCategory.SERVER_ERROR,
            message=message or f"HTTP {status} Server Error",
            status=status,
            url=url_str,
            method=method,
            headers=headers_dict,
        )
    # Unknown/unhandled code
    _log_http_error(
        display_name,
        log_prefix,
        HttpErrorCategory.UNKNOWN,
        f"Unclassified response {status}.",
        message,
        headers_dict,
        logger.warning,
    )
    return HttpErrorAnalysis(
        category=HttpErrorCategory.UNKNOWN,
        message=message or f"HTTP {status} Unclassified",
        status=status,
        url=url_str,
        method=method,
        headers=headers_dict,
    )


def _log_exchange_error(
    display_name: str | None,
    exchange_category: "ExchangeErrorCategory",
    log_msg: str,
    str_error_code: str,
    message: str,
    log_func: Callable[..., None],
) -> None:
    log_func(
        "%s Exchange warning cause %s code=%s, category=%s, orig_message=%s",
        display_name,
        log_msg,
        str_error_code,
        exchange_category.name,
        message,
    )


def analyze_exchange_error(  # noqa: C901, PLR0911, PLR0912
    e: ExchangeResponseError,
    display_name: str | None,
    logger: logging.Logger,
    current_time: int,
) -> ExchangeErrorAnalysis:
    """
    Analyze ExchangeResponseError from a crypto exchange and structure the result.

    Args:
        e: The ExchangeResponseError exception.
        account: Account context (should have .display).
        logger: Logger instance.
        current_time: Current timestamp in milliseconds (used for ban calculations).

    Returns:
        ExchangeErrorAnalysis containing the error category,
        ban_until (if applicable), and the message.
    """
    str_error_code = str(e.code)
    exchange = e.exchange
    message = str(e.message)

    # BingX
    if exchange == "bingx":
        # 100410: frequency rate limit
        if str_error_code == "100410":
            match = re.search(BINGX_UNBLOCK_REGEX, message)
            if match:
                unblock_time = int(match.group(1))
                _log_exchange_error(
                    display_name,
                    ExchangeErrorCategory.RATE_LIMIT_WITH_BAN,
                    f"endpoint rate limited. "
                    f"Skipping requests until {unblock_time} (now={current_time}).",
                    str_error_code,
                    message,
                    logger.warning,
                )
                return ExchangeErrorAnalysis(
                    category=ExchangeErrorCategory.RATE_LIMIT_WITH_BAN,
                    ban_until=unblock_time,
                    message=message,
                )
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.RATE_LIMIT_WITH_BAN,
                "endpoint rate limited, "
                f"but could not parse unblock time from message: {message}",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.RATE_LIMIT_WITH_BAN, message=message
            )
        # 109400: timestamp is invalid
        if str_error_code == "109400":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.BAD_REQUEST,
                "timestamp is invalid",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.BAD_REQUEST, message=message
            )
        # 109500: network issue,please retry later
        if str_error_code == "109500":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.RETRY_LATER,
                "network issue, please retry later",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.RETRY_LATER, message=message
            )
        # 100421: Null timestamp or timestamp mismatch
        if str_error_code == "100421":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.BAD_REQUEST,
                "null timestamp or timestamp mismatch",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.BAD_REQUEST, message=message
            )
        # 100413: Incorrect API key, ban for 5 min (NEW CASE)
        if str_error_code == "100413":
            block_until = current_time + BINGX_API_KEY_BAN_MINUTES * 60 * 1000
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.API_KEY_EXPIRED,
                (
                    f"incorrect apiKey. Banning account for "
                    f"{BINGX_API_KEY_BAN_MINUTES} minutes until "
                    f"{block_until} (now={current_time}). "
                    f"Check and update your API credentials."
                ),
                str_error_code,
                message,
                logger.error,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.API_KEY_EXPIRED,
                ban_until=block_until,
                message=message,
            )

    # Bybit
    if exchange == "bybit":
        # 10002: invalid request, please check your server timestamp
        if str_error_code == "10002":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.BAD_REQUEST,
                "invalid request, timestamp mismatch.",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.BAD_REQUEST, message=message
            )
        # 10000: Server Timeout
        if str_error_code == "10000":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.BAD_REQUEST,
                "server timeout.",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.BAD_REQUEST, message=message
            )
        # 33004: rate limit api key expired (block 5 min)
        if str_error_code == "33004":
            block_until = current_time + BYBIT_API_KEY_BAN_MINUTES * 60 * 1000
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.API_KEY_EXPIRED,
                (
                    f"API key expired. Blocking this account for "
                    f"{BYBIT_API_KEY_BAN_MINUTES} minutes until {block_until} "
                    f"(now={current_time}). "
                    f"Please update your API credentials."
                ),
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.API_KEY_EXPIRED,
                ban_until=block_until,
                message=message,
            )

    # Binance
    # -1003: Too many requests (block for 1 minute)
    if exchange == "binance" and str_error_code == "-1003":
        block_until = current_time + BINANCE_RATE_LIMIT_BAN_MINUTES * 60 * 1000
        _log_exchange_error(
            display_name,
            ExchangeErrorCategory.RATE_LIMIT_WITH_BAN,
            (
                f"rate limited. Blocking this account for "
                f"{BINANCE_RATE_LIMIT_BAN_MINUTES} minutes until {block_until} "
                f"(now={current_time})."
            ),
            str_error_code,
            message,
            logger.warning,
        )
        return ExchangeErrorAnalysis(
            category=ExchangeErrorCategory.RATE_LIMIT_WITH_BAN,
            ban_until=block_until,
            message=message,
        )

    # OKX
    # 50001: Service temporarily unavailable
    # 50102: Timestamp request expired
    # 51290: Trading bot engine currently upgrading
    if exchange == "okx":
        if str_error_code == "50001":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.TEMP_UNAVAILABLE,
                "service temporarily unavailable.",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.TEMP_UNAVAILABLE,
                message=message,
            )
        if str_error_code == "50102":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.RETRY_LATER,
                "timestamp request expired.",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.RETRY_LATER, message=message
            )
        if str_error_code == "51290":
            _log_exchange_error(
                display_name,
                ExchangeErrorCategory.TEMP_UNAVAILABLE,
                "trading bot engine currently upgrading.",
                str_error_code,
                message,
                logger.warning,
            )
            return ExchangeErrorAnalysis(
                category=ExchangeErrorCategory.TEMP_UNAVAILABLE,
                message=message,
            )

    # Kucoin
    # 400002: Invalid KC-API-TIMESTAMP
    if exchange == "kucoin" and str_error_code == "400002":
        _log_exchange_error(
            display_name,
            ExchangeErrorCategory.BAD_REQUEST,
            "invalid KC-API-TIMESTAMP",
            str_error_code,
            message,
            logger.warning,
        )
        return ExchangeErrorAnalysis(
            category=ExchangeErrorCategory.BAD_REQUEST,
            message=message,
        )

    return ExchangeErrorAnalysis(category=ExchangeErrorCategory.UNKNOWN, message=None)
