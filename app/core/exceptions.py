class CurrencyNotFoundError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Currency '{code}' not found.")


class CurrencyInactiveError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Currency '{code}' is inactive.")


class InsufficientStockError(Exception):
    def __init__(self, code: str, requested: float, available: float):
        super().__init__(
            f"Insufficient stock for {code}: requested {requested}, available {available}."
        )


class ExchangeRateNotFoundError(Exception):
    def __init__(self, from_code: str, to_code: str):
        super().__init__(f"No exchange rate found for {from_code} → {to_code}.")


class DuplicateCurrencyError(Exception):
    def __init__(self, code: str):
        super().__init__(f"Currency with code '{code}' already exists.")
