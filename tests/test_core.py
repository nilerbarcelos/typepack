"""Tests for fastpack core functionality."""

import pytest
import fastpack


class TestBasicTypes:
    """Test serialization of basic Python types."""

    def test_none(self):
        data = fastpack.pack(None)
        assert fastpack.unpack(data) is None

    def test_true(self):
        data = fastpack.pack(True)
        assert fastpack.unpack(data) is True

    def test_false(self):
        data = fastpack.pack(False)
        assert fastpack.unpack(data) is False


class TestIntegers:
    """Test integer serialization across all ranges."""

    def test_positive_fixint(self):
        for value in [0, 1, 50, 127]:
            data = fastpack.pack(value)
            assert fastpack.unpack(data) == value

    def test_negative_fixint(self):
        for value in [-1, -15, -32]:
            data = fastpack.pack(value)
            assert fastpack.unpack(data) == value

    def test_uint8(self):
        data = fastpack.pack(200)
        assert fastpack.unpack(data) == 200

    def test_uint16(self):
        data = fastpack.pack(30000)
        assert fastpack.unpack(data) == 30000

    def test_uint32(self):
        data = fastpack.pack(3000000000)
        assert fastpack.unpack(data) == 3000000000

    def test_uint64(self):
        data = fastpack.pack(10000000000000000000)
        assert fastpack.unpack(data) == 10000000000000000000

    def test_int8(self):
        data = fastpack.pack(-100)
        assert fastpack.unpack(data) == -100

    def test_int16(self):
        data = fastpack.pack(-20000)
        assert fastpack.unpack(data) == -20000

    def test_int32(self):
        data = fastpack.pack(-2000000000)
        assert fastpack.unpack(data) == -2000000000

    def test_int64(self):
        data = fastpack.pack(-5000000000000000000)
        assert fastpack.unpack(data) == -5000000000000000000


class TestFloats:
    """Test float serialization."""

    def test_zero(self):
        data = fastpack.pack(0.0)
        assert fastpack.unpack(data) == 0.0

    def test_positive(self):
        data = fastpack.pack(3.14159)
        assert abs(fastpack.unpack(data) - 3.14159) < 1e-10

    def test_negative(self):
        data = fastpack.pack(-2.71828)
        assert abs(fastpack.unpack(data) - (-2.71828)) < 1e-10

    def test_large(self):
        data = fastpack.pack(1e100)
        assert fastpack.unpack(data) == 1e100


class TestStrings:
    """Test string serialization."""

    def test_empty(self):
        data = fastpack.pack("")
        assert fastpack.unpack(data) == ""

    def test_short_fixstr(self):
        value = "hello"
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_max_fixstr(self):
        value = "a" * 31
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_str8(self):
        value = "a" * 100
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_str16(self):
        value = "a" * 300
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_unicode(self):
        value = "Hello, world!"
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_portuguese(self):
        value = "Olá, mundo!"
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_emoji(self):
        value = "Hello 👋 World 🌍"
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value


class TestBytes:
    """Test bytes serialization."""

    def test_empty(self):
        data = fastpack.pack(b"")
        assert fastpack.unpack(data) == b""

    def test_bin8(self):
        value = b"\x00\x01\x02\x03"
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_bin16(self):
        value = b"x" * 300
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value


class TestLists:
    """Test list serialization."""

    def test_empty(self):
        data = fastpack.pack([])
        assert fastpack.unpack(data) == []

    def test_fixarray(self):
        value = [1, 2, 3]
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_mixed_types(self):
        value = [1, "two", 3.0, True, None]
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_nested(self):
        value = [[1, 2], [3, 4], [5, 6]]
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_array16(self):
        value = list(range(100))
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value


class TestDicts:
    """Test dict serialization."""

    def test_empty(self):
        data = fastpack.pack({})
        assert fastpack.unpack(data) == {}

    def test_fixmap(self):
        value = {"name": "Ana", "age": 30}
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_mixed_values(self):
        value = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "null": None,
        }
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_nested(self):
        value = {
            "user": {
                "name": "Ana",
                "address": {"city": "Joinville", "state": "SC"},
            }
        }
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value

    def test_with_list_values(self):
        value = {"items": [1, 2, 3], "tags": ["python", "serialization"]}
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value


class TestComplexStructures:
    """Test complex nested structures."""

    def test_api_response(self):
        value = {
            "status": "success",
            "data": {
                "users": [
                    {"id": 1, "name": "Ana", "active": True},
                    {"id": 2, "name": "Bruno", "active": False},
                ],
                "total": 2,
            },
            "meta": {"page": 1, "per_page": 20},
        }
        data = fastpack.pack(value)
        assert fastpack.unpack(data) == value


class TestErrors:
    """Test error handling."""

    def test_unsupported_type(self):
        with pytest.raises(TypeError):
            fastpack.pack(object())

    def test_unsupported_set(self):
        with pytest.raises(TypeError):
            fastpack.pack({1, 2, 3})


class TestBinarySize:
    """Test that binary output is compact."""

    def test_smaller_than_json(self):
        import json

        value = {"name": "Ana", "age": 30, "active": True}
        packed = fastpack.pack(value)
        json_bytes = json.dumps(value).encode("utf-8")
        assert len(packed) < len(json_bytes)
