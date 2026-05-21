"""
currency_utils.py
Centralized currency conversion utility for the SMART TOURISM APP backend.
- Fetches and caches exchange rates from a public API.
- Provides conversion functions for use in endpoints/services.
"""

import requests
import time
from typing import Dict

# You can use a free API key from exchangerate-api.com or openexchangerates.org
EXCHANGE_API_URL = "https://api.exchangerate-api.com/v4/latest/{}"  # e.g., USD
CACHE_TTL = 3600  # 1 hour

class CurrencyConverter:
    _cache: Dict[str, Dict] = {}
    _cache_time: Dict[str, float] = {}

    @classmethod
    def get_rates(cls, base_currency: str) -> Dict[str, float]:
        now = time.time()
        if (
            base_currency in cls._cache
            and now - cls._cache_time[base_currency] < CACHE_TTL
        ):
            return cls._cache[base_currency]
        resp = requests.get(EXCHANGE_API_URL.format(base_currency))
        resp.raise_for_status()
        data = resp.json()
        rates = data["rates"]
        cls._cache[base_currency] = rates
        cls._cache_time[base_currency] = now
        return rates

    @classmethod
    def convert(cls, amount: float, from_currency: str, to_currency: str) -> float:
        if from_currency == to_currency:
            return amount
        rates = cls.get_rates(from_currency.upper())
        rate = rates.get(to_currency.upper())
        if not rate:
            raise ValueError(f"No rate for {to_currency}")
        return amount * rate

    @classmethod
    def supported_currencies(cls, base_currency: str = "USD"):
        return list(cls.get_rates(base_currency).keys())

# Example usage:
# amount_in_kes = CurrencyConverter.convert(100, "USD", "KES")
# print(amount_in_kes)
