"""Time parsing utilities for CLI flags."""

import re

# Conversion factors to seconds
TIME_UNITS = {
    "s": 1,
    "m": 60,
    "h": 3600,
    "d": 86400,
}


def parse_time(value: str, default_unit: str = "s") -> float:
    """
    Parse a time string to seconds.

    Supports formats:
    - "5s", "2.5m", "1h", "0.5d" (with unit)
    - "5", "2.5" (plain number, uses default_unit)

    Args:
        value: Time string to parse
        default_unit: Unit to use if none specified ("s", "m", "h", "d")

    Returns:
        Time in seconds as float

    Raises:
        ValueError: If format is invalid or value is negative
    """
    value = value.strip()

    # Try to match number + optional unit (any single letter)
    match = re.match(r"^(-?\d+\.?\d*)\s*([a-zA-Z]?)$", value)
    if not match:
        raise ValueError(f"Invalid time format: '{value}'. Use format like '5s', '2.5m', '1h', '0.5d'")

    number_str, unit = match.groups()
    number = float(number_str)

    if number < 0:
        raise ValueError(f"Time value must be positive: '{value}'")

    # Use default unit if none provided
    unit = unit.lower() if unit else default_unit.lower()

    if unit not in TIME_UNITS:
        raise ValueError(f"Invalid time unit: '{unit}'. Use 's', 'm', 'h', or 'd'")

    return number * TIME_UNITS[unit]
