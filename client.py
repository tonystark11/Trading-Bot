from __future__ import annotations

import hashlib
import hmac
import time
from typing import Any
from urllib.parse import urlencode

import requests

from bot.logging_config import setup_logging

BASE_URL = "https://testnet.binance.vision"
logger = setup_logging()


class BinanceClientError(Exception):
    pass


class BinanceClient:
    def __init__(self, api_key: str, api_secret: str) -> None:
        if not api_key or not api_secret:
            raise ValueError("api_key and api_secret must not be empty.")
        self._api_key = api_key
        self._api_secret = api_secret.encode()
        self._session = requests.Session()
        self._session.headers.update({"X-MBX-APIKEY": self._api_key})

    def _sign(self, params: dict) -> dict:
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(self._api_secret, query_string.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def _get(self, path: str, params: dict | None = None) -> Any:
        url = BASE_URL + path
        params = self._sign(params or {})
        logger.debug(f"GET {url} params={params}")
        try:
            resp = self._session.get(url, params=params, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Network error: {exc}")
            raise BinanceClientError(f"Network error: {exc}") from exc
        return self._handle_response(resp)

    def _post(self, path: str, params: dict) -> Any:
        url = BASE_URL + path
        params = self._sign(params)
        logger.debug(f"POST {url} params={params}")
        try:
            resp = self._session.post(url, params=params, timeout=10)
        except requests.exceptions.RequestException as exc:
            logger.error(f"Network error: {exc}")
            raise BinanceClientError(f"Network error: {exc}") from exc
        return self._handle_response(resp)

    @staticmethod
    def _handle_response(resp: requests.Response) -> Any:
        logger.debug(f"Response [{resp.status_code}]: {resp.text[:500]}")
        try:
            data = resp.json()
        except ValueError:
            raise BinanceClientError(f"Non-JSON response: {resp.text}")

        if isinstance(data, dict) and "code" in data and data["code"] != 200:
            msg = data.get("msg", "Unknown API error")
            code = data["code"]
            logger.error(f"API error {code}: {msg}")
            raise BinanceClientError(f"API error {code}: {msg}")

        resp.raise_for_status()
        return data

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: float | None = None,
        stop_price: float | None = None,
        time_in_force: str = "GTC",
    ) -> dict:
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }
        if order_type == "LIMIT":
            params["price"] = price
            params["timeInForce"] = time_in_force
        elif order_type == "STOP_LOSS":
            params["stopPrice"] = stop_price
            params["timeInForce"] = time_in_force

        logger.info(f"Placing order: {params}")
        result = self._post("/api/v3/order", params)
        logger.info(f"Order response: {result}")
        return result
