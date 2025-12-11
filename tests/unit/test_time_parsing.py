# tests/unit/test_time_parsing.py
import pytest
from spraycharles.lib.utils.time import parse_time


@pytest.mark.unit
class TestParseTime:
    """Tests for parse_time() utility."""

    def test_seconds_with_unit(self):
        assert parse_time("5s") == 5.0
        assert parse_time("1.5s") == 1.5
        assert parse_time("0.5s") == 0.5

    def test_minutes_with_unit(self):
        assert parse_time("2m") == 120.0
        assert parse_time("1.5m") == 90.0
        assert parse_time("0.5m") == 30.0

    def test_hours_with_unit(self):
        assert parse_time("1h") == 3600.0
        assert parse_time("2.5h") == 9000.0

    def test_days_with_unit(self):
        assert parse_time("1d") == 86400.0
        assert parse_time("0.5d") == 43200.0

    def test_plain_number_default_seconds(self):
        assert parse_time("5", default_unit="s") == 5.0
        assert parse_time("10", default_unit="s") == 10.0

    def test_plain_number_default_minutes(self):
        assert parse_time("5", default_unit="m") == 300.0
        assert parse_time("30", default_unit="m") == 1800.0

    def test_plain_float_default_seconds(self):
        assert parse_time("2.5", default_unit="s") == 2.5

    def test_plain_float_default_minutes(self):
        assert parse_time("1.5", default_unit="m") == 90.0

    def test_case_insensitive_units(self):
        assert parse_time("5S") == 5.0
        assert parse_time("2M") == 120.0
        assert parse_time("1H") == 3600.0
        assert parse_time("1D") == 86400.0

    def test_invalid_unit_raises(self):
        with pytest.raises(ValueError, match="Invalid time unit"):
            parse_time("5x")

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            parse_time("abc")

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="must be positive"):
            parse_time("-5s")

    def test_zero_allowed(self):
        assert parse_time("0s") == 0.0
        assert parse_time("0", default_unit="s") == 0.0
