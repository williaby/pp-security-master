import re
from decimal import Decimal

from .models import SecurityMaster


class SecurityDataValidator:
    """Validates security data for quality and completeness."""

    # ISIN validation pattern
    ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

    # WKN validation pattern (German securities)
    WKN_PATTERN = re.compile(r"^[A-Z0-9]{6}$")

    # Symbol validation (basic pattern)
    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9._-]{1,20}$")

    @classmethod
    def validate_isin(cls, isin: str | None) -> bool:
        """Validate ISIN format and check digit."""
        if not isin:
            return True  # Optional field

        if not cls.ISIN_PATTERN.match(isin):
            return False

        # ISIN check digit validation
        chars = []
        for char in isin[:-1]:
            if char.isdigit():
                chars.append(char)
            else:
                chars.extend(str(ord(char) - ord("A") + 10))

        num_str = "".join(chars)
        check_sum = sum(
            int(digit) * (2 if i % 2 == 0 else 1)
            for i, digit in enumerate(reversed(num_str))
        )

        return (10 - (check_sum % 10)) % 10 == int(isin[-1])

    @classmethod
    def validate_wkn(cls, wkn: str | None) -> bool:
        """Validate WKN format."""
        if not wkn:
            return True  # Optional field
        return bool(cls.WKN_PATTERN.match(wkn))

    @classmethod
    def validate_symbol(cls, symbol: str | None) -> bool:
        """Validate trading symbol format."""
        if not symbol:
            return True  # Optional field
        return bool(cls.SYMBOL_PATTERN.match(symbol))

    @classmethod
    def validate_currency(cls, currency: str) -> bool:
        """Validate currency code (ISO 4217)."""
        return bool(currency and len(currency) == 3 and currency.isupper())

    @classmethod
    def calculate_data_quality_score(cls, security: SecurityMaster) -> Decimal:
        """Calculate data quality score (0.00-1.00) based on completeness and validity."""
        score = Decimal("0.0")

        # Core identification (40% weight)
        identification_score = 0
        identification_checks = 0

        if security.name:
            identification_score += 1
        identification_checks += 1

        if cls.validate_isin(security.isin) and security.isin:
            identification_score += 2  # ISIN is most important
        identification_checks += 2

        if cls.validate_symbol(security.symbol) and security.symbol:
            identification_score += 1
        identification_checks += 1

        if cls.validate_wkn(security.wkn) and security.wkn:
            identification_score += 1
        identification_checks += 1

        score += Decimal(str(identification_score / identification_checks * 0.4))

        # Pricing data (20% weight)
        pricing_score = 0
        pricing_checks = 0

        if security.latest_price is not None:
            pricing_score += 1
        pricing_checks += 1

        if security.latest_date:
            pricing_score += 1
        pricing_checks += 1

        if security.currency and cls.validate_currency(security.currency):
            pricing_score += 1
        pricing_checks += 1

        if pricing_checks > 0:
            score += Decimal(str(pricing_score / pricing_checks * 0.2))

        # Classifications (30% weight)
        classification_score = 0
        classification_checks = 0

        classification_fields = [
            security.sector,
            security.type_of_security_level1,
            security.asset_classes_level1,
            security.region,
            security.market,
        ]

        for field in classification_fields:
            if field:
                classification_score += 1
            classification_checks += 1

        if classification_checks > 0:
            score += Decimal(str(classification_score / classification_checks * 0.3))

        # Data sources and feeds (10% weight)
        source_score = 0
        source_checks = 0

        if security.quote_feed_latest:
            source_score += 1
        source_checks += 1

        if security.data_source:
            source_score += 1
        source_checks += 1

        if source_checks > 0:
            score += Decimal(str(source_score / source_checks * 0.1))

        return min(score, Decimal("1.00"))

    @classmethod
    def validate_security(cls, security: SecurityMaster) -> tuple[bool, list[str]]:
        """Validate a security record and return validation status and errors."""
        errors = []

        # Required fields
        if not security.name:
            errors.append("Name is required")

        if not security.currency:
            errors.append("Currency is required")
        elif not cls.validate_currency(security.currency):
            errors.append(f"Invalid currency code: {security.currency}")

        # Format validations
        if not cls.validate_isin(security.isin):
            errors.append(f"Invalid ISIN: {security.isin}")

        if not cls.validate_wkn(security.wkn):
            errors.append(f"Invalid WKN: {security.wkn}")

        if not cls.validate_symbol(security.symbol):
            errors.append(f"Invalid symbol: {security.symbol}")

        # Business rule validations
        if security.latest_price is not None and security.latest_price < 0:
            errors.append("Latest price cannot be negative")

        if security.ter is not None and (security.ter < 0 or security.ter > 10):
            errors.append("TER must be between 0% and 10%")

        return len(errors) == 0, errors
