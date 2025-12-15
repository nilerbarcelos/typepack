"""Tests for fastpack extended types (v0.2.0)."""

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID

import fastpack


class TestDatetime:
    """Test datetime serialization."""

    def test_datetime_now(self):
        value = datetime(2024, 12, 15, 14, 30, 45)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_datetime_with_microseconds(self):
        value = datetime(2024, 1, 1, 12, 0, 0, 123456)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_datetime_min(self):
        value = datetime(1, 1, 1, 0, 0, 0)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestDate:
    """Test date serialization."""

    def test_date_today(self):
        value = date(2024, 12, 15)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_date_min(self):
        value = date(1, 1, 1)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_date_max(self):
        value = date(9999, 12, 31)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestTime:
    """Test time serialization."""

    def test_time_noon(self):
        value = time(12, 0, 0)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_time_with_microseconds(self):
        value = time(14, 30, 45, 123456)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_time_midnight(self):
        value = time(0, 0, 0)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestTimedelta:
    """Test timedelta serialization."""

    def test_timedelta_days(self):
        value = timedelta(days=5)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_timedelta_hours(self):
        value = timedelta(hours=3, minutes=30)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_timedelta_negative(self):
        value = timedelta(days=-1)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_timedelta_complex(self):
        value = timedelta(days=2, hours=5, minutes=30, seconds=15, microseconds=500)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        # Compare total seconds due to floating point
        assert abs(result.total_seconds() - value.total_seconds()) < 0.001


class TestDecimal:
    """Test Decimal serialization."""

    def test_decimal_integer(self):
        value = Decimal("123")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_decimal_float(self):
        value = Decimal("123.456")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_decimal_negative(self):
        value = Decimal("-99.99")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_decimal_scientific(self):
        value = Decimal("1.23E+10")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_decimal_precision(self):
        value = Decimal("0.123456789012345678901234567890")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestUUID:
    """Test UUID serialization."""

    def test_uuid_random(self):
        value = UUID("12345678-1234-5678-1234-567812345678")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_uuid_nil(self):
        value = UUID("00000000-0000-0000-0000-000000000000")
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestTuple:
    """Test tuple serialization."""

    def test_empty(self):
        value = ()
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, tuple)

    def test_simple(self):
        value = (1, 2, 3)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, tuple)

    def test_mixed(self):
        value = (1, "two", 3.0)
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, tuple)

    def test_nested(self):
        value = ((1, 2), (3, 4))
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value


class TestSet:
    """Test set serialization."""

    def test_empty(self):
        value = set()
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, set)

    def test_integers(self):
        value = {1, 2, 3}
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, set)

    def test_strings(self):
        value = {"apple", "banana", "cherry"}
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, set)


class TestFrozenset:
    """Test frozenset serialization."""

    def test_empty(self):
        value = frozenset()
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, frozenset)

    def test_integers(self):
        value = frozenset([1, 2, 3])
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value
        assert isinstance(result, frozenset)


class Color(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DONE = "done"


class TestEnum:
    """Test Enum serialization."""

    def test_int_enum(self):
        value = Color.RED
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result["__enum__"] is True
        assert result["name"] == "RED"
        assert result["value"] == 1

    def test_str_enum(self):
        value = Status.ACTIVE
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result["__enum__"] is True
        assert result["name"] == "ACTIVE"
        assert result["value"] == "active"


class TestComplexStructures:
    """Test complex structures with new types."""

    def test_dict_with_datetime(self):
        value = {
            "created_at": datetime(2024, 12, 15, 10, 30, 0),
            "name": "Test",
        }
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result["created_at"] == value["created_at"]
        assert result["name"] == value["name"]

    def test_list_of_uuids(self):
        value = [
            UUID("11111111-1111-1111-1111-111111111111"),
            UUID("22222222-2222-2222-2222-222222222222"),
        ]
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result == value

    def test_api_response_with_types(self):
        value = {
            "id": UUID("12345678-1234-5678-1234-567812345678"),
            "amount": Decimal("99.99"),
            "created_at": datetime(2024, 12, 15, 14, 30, 0),
            "tags": {"new", "featured"},
            "coordinates": (40.7128, -74.0060),
        }
        data = fastpack.pack(value)
        result = fastpack.unpack(data)
        assert result["id"] == value["id"]
        assert result["amount"] == value["amount"]
        assert result["created_at"] == value["created_at"]
        assert result["tags"] == value["tags"]
        assert result["coordinates"] == value["coordinates"]
