from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .env import is_placeholder


DEFAULT_BASE_URL = "https://api2.capitalist.net"


class CapitalistError(RuntimeError):
    """Raised when the Capitalist API returns an error response."""

    def __init__(self, message: str, *, status: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


@dataclass(frozen=True)
class CapitalistCredentials:
    api_key: str
    api_secret: str

    @classmethod
    def from_env(cls) -> "CapitalistCredentials":
        api_key = os.environ.get("CAPITALIST_API_KEY")
        api_secret = os.environ.get("CAPITALIST_API_SECRET")
        if is_placeholder(api_key) or is_placeholder(api_secret):
            raise CapitalistError(
                "Set CAPITALIST_API_KEY and CAPITALIST_API_SECRET before calling the Capitalist API."
            )
        return cls(api_key=api_key, api_secret=api_secret)


def compact_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def calculate_signature(timestamp_ms: str, body: str, api_secret: str) -> str:
    raw = f"{timestamp_ms}{body}{api_secret}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class CapitalistClient:
    def __init__(
        self,
        credentials: CapitalistCredentials | None = None,
        *,
        base_url: str | None = None,
        timeout: float = 30,
    ) -> None:
        self.credentials = credentials or CapitalistCredentials.from_env()
        self.base_url = (base_url or os.environ.get("CAPITALIST_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> Any:
        method = method.upper()
        body = "" if json_body is None else compact_json(json_body)
        timestamp_ms = str(int(time.time() * 1000))
        signature = calculate_signature(timestamp_ms, body, self.credentials.api_secret)

        url = self._build_url(path, params)
        data = body.encode("utf-8") if body else None
        headers = {
            "API-Key": self.credentials.api_key,
            "X-Request-Timestamp": timestamp_ms,
            "Signature": signature,
            "Accept": "application/json",
        }
        if body:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return self._decode_response(response.status, response.read())
        except urllib.error.HTTPError as exc:
            payload = self._decode_error_payload(exc.read())
            message = self._extract_error_message(payload) or f"Capitalist API HTTP {exc.code}"
            raise CapitalistError(message, status=exc.code, payload=payload) from exc
        except urllib.error.URLError as exc:
            raise CapitalistError(f"Capitalist API request failed: {exc.reason}") from exc

    def list_accounts(self, currency: str) -> Any:
        return self.request("GET", "/v1/account/list", params={"currency": currency})

    def exchange_rate(self, currency_from: str, currency_to: str) -> Any:
        return self.request("GET", "/v1/rate", params={"from": currency_from, "to": currency_to})

    def deposit_address(self, account: str, currency: str) -> str:
        payload = self.request("GET", f"/v1/depositAddress/{self._quote_path(account)}", params={"currency": currency})
        return self._extract_address(payload)

    def usdt_trc20_autoconvert_address(self, account: str) -> str:
        payload = self.request("GET", f"/v1/depositAddressAutoUSDTt/{self._quote_path(account)}")
        return self._extract_address(payload)

    def payment_status_by_document(self, document_id: int | str) -> Any:
        return self.request("GET", f"/v1/payment/document/{self._quote_path(str(document_id))}")

    def payment_status_by_request(self, user_request_id: str) -> Any:
        return self.request("GET", f"/v1/payment/{self._quote_path(user_request_id)}")

    def whitelist(self) -> Any:
        return self.request("GET", "/v1/whitelist")

    def add_whitelist_ips(self, ips: list[str]) -> Any:
        return self.request("POST", "/v1/whitelist", json_body={"ip": ips})

    def remove_whitelist_ips(self, ips: list[str]) -> Any:
        return self.request("POST", "/v1/whitelist/remove", json_body={"ip": ips})

    def _build_url(self, path: str, params: dict[str, Any] | None) -> str:
        clean_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{clean_path}"
        if params:
            query = urllib.parse.urlencode({key: value for key, value in params.items() if value is not None})
            if query:
                url = f"{url}?{query}"
        return url

    @staticmethod
    def _quote_path(value: str) -> str:
        return urllib.parse.quote(value, safe="")

    @staticmethod
    def _extract_address(payload: Any) -> str:
        if isinstance(payload, dict) and isinstance(payload.get("address"), str):
            return payload["address"]
        raise CapitalistError("Capitalist API response does not contain an address.", payload=payload)

    @staticmethod
    def _decode_response(status: int, raw: bytes) -> Any:
        if not raw:
            return None
        text = raw.decode("utf-8")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise CapitalistError(f"Capitalist API returned non-JSON response with HTTP {status}.") from exc

    @staticmethod
    def _decode_error_payload(raw: bytes) -> Any:
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return raw.decode("utf-8", errors="replace")

    @staticmethod
    def _extract_error_message(payload: Any) -> str | None:
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload["error"])
        if isinstance(payload, str) and payload.strip():
            return payload.strip()
        return None
