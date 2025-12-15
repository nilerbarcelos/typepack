"""Tests for fastpack extensibility features (v0.3.0)."""

import pytest
from dataclasses import dataclass
from typing import NamedTuple

import fastpack


class TestDataclass:
    """Tests for dataclass serialization."""

    def test_simple_dataclass(self):
        @dataclass
        class User:
            name: str
            age: int

        user = User("Ana", 30)
        data = fastpack.pack(user)
        result = fastpack.unpack(data)

        assert result["__dataclass__"] == "User"
        assert result["name"] == "Ana"
        assert result["age"] == 30

    def test_dataclass_with_optional(self):
        @dataclass
        class Product:
            name: str
            price: float
            description: str = None

        product = Product("Widget", 9.99)
        data = fastpack.pack(product)
        result = fastpack.unpack(data)

        assert result["__dataclass__"] == "Product"
        assert result["name"] == "Widget"
        assert result["price"] == 9.99
        assert result["description"] is None

    def test_dataclass_with_nested_types(self):
        @dataclass
        class Address:
            street: str
            city: str

        @dataclass
        class Person:
            name: str
            address: dict  # Nested as dict since Address won't be reconstructed

        address = Address("123 Main St", "Springfield")
        person = Person("John", {"street": "123 Main St", "city": "Springfield"})

        data = fastpack.pack(person)
        result = fastpack.unpack(data)

        assert result["__dataclass__"] == "Person"
        assert result["name"] == "John"
        assert result["address"]["street"] == "123 Main St"

    def test_dataclass_with_list(self):
        @dataclass
        class Order:
            id: int
            items: list

        order = Order(123, ["apple", "banana", "cherry"])
        data = fastpack.pack(order)
        result = fastpack.unpack(data)

        assert result["__dataclass__"] == "Order"
        assert result["id"] == 123
        assert result["items"] == ["apple", "banana", "cherry"]


class TestNamedTuple:
    """Tests for NamedTuple serialization."""

    def test_simple_namedtuple(self):
        class Point(NamedTuple):
            x: int
            y: int

        point = Point(10, 20)
        data = fastpack.pack(point)
        result = fastpack.unpack(data)

        assert result["__namedtuple__"] == "Point"
        assert result["x"] == 10
        assert result["y"] == 20

    def test_namedtuple_with_defaults(self):
        class Config(NamedTuple):
            host: str
            port: int = 8080

        config = Config("localhost")
        data = fastpack.pack(config)
        result = fastpack.unpack(data)

        assert result["__namedtuple__"] == "Config"
        assert result["host"] == "localhost"
        assert result["port"] == 8080

    def test_namedtuple_with_mixed_types(self):
        class Record(NamedTuple):
            id: int
            name: str
            active: bool
            score: float

        record = Record(1, "Test", True, 95.5)
        data = fastpack.pack(record)
        result = fastpack.unpack(data)

        assert result["__namedtuple__"] == "Record"
        assert result["id"] == 1
        assert result["name"] == "Test"
        assert result["active"] is True
        assert result["score"] == 95.5


class TestRegister:
    """Tests for @fastpack.register decorator."""

    def setup_method(self):
        """Clear registry before each test."""
        fastpack.clear_registry()

    def test_register_with_custom_encode_decode(self):
        @fastpack.register
        class Money:
            def __init__(self, amount: int, currency: str):
                self.amount = amount
                self.currency = currency

            def __fastpack_encode__(self):
                return {"amount": self.amount, "currency": self.currency}

            @classmethod
            def __fastpack_decode__(cls, data):
                return cls(data["amount"], data["currency"])

            def __eq__(self, other):
                return self.amount == other.amount and self.currency == other.currency

        money = Money(1000, "USD")
        data = fastpack.pack(money)
        result = fastpack.unpack(data)

        assert isinstance(result, Money)
        assert result.amount == 1000
        assert result.currency == "USD"

    def test_register_dataclass(self):
        @fastpack.register
        @dataclass
        class Point3D:
            x: float
            y: float
            z: float

        point = Point3D(1.0, 2.0, 3.0)
        data = fastpack.pack(point)
        result = fastpack.unpack(data)

        assert isinstance(result, Point3D)
        assert result.x == 1.0
        assert result.y == 2.0
        assert result.z == 3.0

    def test_register_namedtuple(self):
        class Color(NamedTuple):
            r: int
            g: int
            b: int

        fastpack.register(Color)

        color = Color(255, 128, 0)
        data = fastpack.pack(color)
        result = fastpack.unpack(data)

        assert isinstance(result, Color)
        assert result.r == 255
        assert result.g == 128
        assert result.b == 0

    def test_register_with_explicit_type_code(self):
        @fastpack.register(type_code=0x30)
        class CustomType:
            def __init__(self, value: str):
                self.value = value

            def __fastpack_encode__(self):
                return self.value

            @classmethod
            def __fastpack_decode__(cls, data):
                return cls(data)

        obj = CustomType("test")
        data = fastpack.pack(obj)
        result = fastpack.unpack(data)

        assert isinstance(result, CustomType)
        assert result.value == "test"

    def test_duplicate_type_code_raises(self):
        @fastpack.register(type_code=0x50)
        class TypeA:
            def __fastpack_encode__(self):
                return {}

            @classmethod
            def __fastpack_decode__(cls, data):
                return cls()

        with pytest.raises(ValueError, match="already registered"):
            @fastpack.register(type_code=0x50)
            class TypeB:
                def __fastpack_encode__(self):
                    return {}

                @classmethod
                def __fastpack_decode__(cls, data):
                    return cls()

    def test_register_without_encode_decode_raises(self):
        with pytest.raises(TypeError, match="must have __fastpack_encode__"):
            @fastpack.register
            class InvalidType:
                pass


class TestMixedStructures:
    """Tests for complex structures with dataclasses and namedtuples."""

    def test_dict_with_dataclass(self):
        @dataclass
        class Item:
            name: str
            price: float

        item = Item("Coffee", 4.50)
        data = fastpack.pack({"item": item, "quantity": 2})
        result = fastpack.unpack(data)

        assert result["quantity"] == 2
        assert result["item"]["__dataclass__"] == "Item"
        assert result["item"]["name"] == "Coffee"
        assert result["item"]["price"] == 4.50

    def test_list_of_namedtuples(self):
        class Coord(NamedTuple):
            lat: float
            lng: float

        coords = [Coord(10.0, 20.0), Coord(30.0, 40.0)]
        data = fastpack.pack(coords)
        result = fastpack.unpack(data)

        assert len(result) == 2
        assert result[0]["__namedtuple__"] == "Coord"
        assert result[0]["lat"] == 10.0
        assert result[1]["lng"] == 40.0

    def test_dataclass_not_confused_with_dict(self):
        """Ensure dataclass is packed as ext, not as regular dict."""
        @dataclass
        class Config:
            debug: bool
            version: str

        config = Config(True, "1.0.0")
        regular_dict = {"debug": True, "version": "1.0.0"}

        config_data = fastpack.pack(config)
        dict_data = fastpack.pack(regular_dict)

        config_result = fastpack.unpack(config_data)
        dict_result = fastpack.unpack(dict_data)

        # Dataclass should have __dataclass__ marker
        assert "__dataclass__" in config_result
        assert "__dataclass__" not in dict_result

    def test_namedtuple_not_confused_with_tuple(self):
        """Ensure NamedTuple is packed as ext, not as regular tuple."""
        class Version(NamedTuple):
            major: int
            minor: int

        named = Version(1, 2)
        regular = (1, 2)

        named_data = fastpack.pack(named)
        tuple_data = fastpack.pack(regular)

        named_result = fastpack.unpack(named_data)
        tuple_result = fastpack.unpack(tuple_data)

        # NamedTuple should be a dict with __namedtuple__ marker
        assert isinstance(named_result, dict)
        assert "__namedtuple__" in named_result

        # Regular tuple should be a tuple
        assert isinstance(tuple_result, tuple)
