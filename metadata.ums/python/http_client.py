from __future__ import annotations

import json
import time
import threading
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Optional


class RateLimiter:
    """Token bucket rate limiter, thread-safe via threading.Lock."""

    def __init__(self, max_requests_per_second: float) -> None:
        self._max_rate = max_requests_per_second
        self._tokens = max_requests_per_second
        self._last_refill = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a token is available."""
        while True:
            with self._lock:
                now = time.monotonic()
                elapsed = now - self._last_refill
                self._tokens = min(
                    self._max_rate,
                    self._tokens + elapsed * self._max_rate,
                )
                self._last_refill = now

                if self._tokens >= 1.0:
                    self._tokens -= 1.0
                    return

            time.sleep(0.05)


class HttpError(Exception):
    """HTTP error with status code, message, and originating URL."""

    def __init__(self, status_code: int, message: str, url: str) -> None:
        self.status_code = status_code
        self.message = message
        self.url = url
        super().__init__(
            f"HTTP {status_code} for {url}: {message}"
        )


class HttpClient:
    """urllib-based HTTP client with retry, rate limiting, and logging."""

    DEFAULT_TIMEOUT = 15
    MAX_RETRIES = 3
    BACKOFF_BASE = 1.0
    BACKOFF_MULTIPLIER = 2.0
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        base_url: str,
        headers: Optional[dict] = None,
        rate_limiter: Optional[RateLimiter] = None,
        timeout: int = DEFAULT_TIMEOUT,
        logger: Optional[Any] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = headers or {}
        self._rate_limiter = rate_limiter
        self._timeout = timeout
        self._logger = logger

    def get_json(self, path: str, params: Optional[dict] = None) -> dict:
        """Send GET request, parse JSON response with retry logic.

        Args:
            path: URL path to append to the base URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            HttpError: On non-retryable HTTP errors or after all retries
                are exhausted.
        """
        url = self._build_url(path, params)
        last_error: Optional[Exception] = None

        for attempt in range(1, self.MAX_RETRIES + 1):
            if self._rate_limiter is not None:
                self._rate_limiter.acquire()

            self._log_debug(
                f"HTTP GET {url} (attempt {attempt}/{self.MAX_RETRIES})"
            )

            try:
                req = urllib.request.Request(url, headers=self._headers)
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    body = resp.read().decode("utf-8")
                    result = json.loads(body)

                self._log_debug(f"HTTP GET {url} -> 200 OK")
                return result

            except urllib.error.HTTPError as exc:
                status = exc.code
                reason = str(exc.reason) if exc.reason else "Unknown"

                if status not in self.RETRYABLE_STATUS_CODES:
                    self._log_error(
                        f"HTTP GET {url} -> {status} {reason} (non-retryable)"
                    )
                    raise HttpError(status, reason, url) from exc

                self._log_warning(
                    f"HTTP GET {url} -> {status} {reason} "
                    f"(attempt {attempt}/{self.MAX_RETRIES})"
                )
                last_error = HttpError(status, reason, url)

            except urllib.error.URLError as exc:
                self._log_warning(
                    f"HTTP GET {url} -> URLError: {exc.reason} "
                    f"(attempt {attempt}/{self.MAX_RETRIES})"
                )
                last_error = exc

            except Exception as exc:
                self._log_error(
                    f"HTTP GET {url} -> unexpected error: {exc} "
                    f"(attempt {attempt}/{self.MAX_RETRIES})"
                )
                last_error = exc

            if attempt < self.MAX_RETRIES:
                backoff = self.BACKOFF_BASE * (
                    self.BACKOFF_MULTIPLIER ** (attempt - 1)
                )
                self._log_debug(f"Retrying in {backoff:.1f}s...")
                time.sleep(backoff)

        self._log_error(
            f"HTTP GET {url} -> all {self.MAX_RETRIES} retries exhausted"
        )
        raise last_error  # type: ignore[misc]

    def get_json_degraded(self, path: str, params: Optional[dict] = None) -> dict:
        """GET request in degraded mode: 0 retries, 5s timeout.

        Args:
            path: URL path to append to the base URL.
            params: Optional query parameters.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            HttpError: On HTTP errors (no retry).
        """
        url = self._build_url(path, params)

        if self._rate_limiter is not None:
            self._rate_limiter.acquire()

        self._log_debug(f"HTTP GET {url} (degraded mode, timeout=5s)")

        try:
            req = urllib.request.Request(url, headers=self._headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)

            self._log_debug(f"HTTP GET {url} -> 200 OK (degraded mode)")
            return result

        except urllib.error.HTTPError as exc:
            status = exc.code
            reason = str(exc.reason) if exc.reason else "Unknown"
            self._log_warning(
                f"HTTP GET {url} -> {status} {reason} "
                f"(degraded mode, no retry)"
            )
            raise HttpError(status, reason, url) from exc

        except urllib.error.URLError as exc:
            self._log_warning(
                f"HTTP GET {url} -> URLError: {exc.reason} "
                f"(degraded mode, no retry)"
            )
            raise

        except Exception as exc:
            self._log_error(
                f"HTTP GET {url} -> unexpected error: {exc} "
                f"(degraded mode, no retry)"
            )
            raise

    def _build_url(self, path: str, params: Optional[dict] = None) -> str:
        """Build full URL from base, path, and optional query parameters."""
        path = path.lstrip("/")
        url = f"{self._base_url}/{path}" if path else self._base_url

        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"

        return url

    def _log_debug(self, message: str) -> None:
        if self._logger is not None:
            self._logger.debug(message)

    def _log_warning(self, message: str) -> None:
        if self._logger is not None:
            self._logger.warning(message)

    def _log_error(self, message: str) -> None:
        if self._logger is not None:
            self._logger.error(message)
