"""
Type registry and extension system for fastpack.

Allows registering custom types with encode/decode functions.
"""

from dataclasses import fields, is_dataclass
from typing import Any, Callable, NamedTuple, Type, get_type_hints

# Registry for custom types
_type_registry: dict[Type, tuple[int, Callable, Callable]] = {}
_type_code_registry: dict[int, tuple[Type, Callable]] = {}

# Start custom type codes after built-in ones (0x01-0x0A)
_next_type_code = 0x10


def register(cls: Type = None, *, type_code: int = None):
    """
    Register a custom type for serialization.

    Can be used as a decorator or called directly.

    Usage as decorator:
        @fastpack.register
        class MyClass:
            ...

    Usage with explicit type code:
        @fastpack.register(type_code=0x20)
        class MyClass:
            ...

    The class must have either:
    - __fastpack_encode__ and __fastpack_decode__ methods
    - Be a dataclass (auto-handled)
    - Be a NamedTuple (auto-handled)
    """
    def decorator(cls: Type) -> Type:
        _register_type(cls, type_code)
        return cls

    if cls is not None:
        # Called without arguments: @register
        return decorator(cls)
    else:
        # Called with arguments: @register(type_code=0x20)
        return decorator


def _register_type(cls: Type, type_code: int = None) -> None:
    """Internal function to register a type."""
    global _next_type_code

    if type_code is None:
        type_code = _next_type_code
        _next_type_code += 1

    if type_code in _type_code_registry:
        existing = _type_code_registry[type_code][0]
        raise ValueError(f"Type code {type_code} already registered for {existing}")

    # Determine encode/decode functions
    if hasattr(cls, "__fastpack_encode__") and hasattr(cls, "__fastpack_decode__"):
        encode_fn = cls.__fastpack_encode__
        decode_fn = cls.__fastpack_decode__
    elif is_dataclass(cls):
        encode_fn = _dataclass_encode
        decode_fn = lambda data: _dataclass_decode(cls, data)
    elif _is_namedtuple(cls):
        encode_fn = _namedtuple_encode
        decode_fn = lambda data: _namedtuple_decode(cls, data)
    else:
        raise TypeError(
            f"Type {cls.__name__} must have __fastpack_encode__ and "
            "__fastpack_decode__ methods, or be a dataclass/NamedTuple"
        )

    _type_registry[cls] = (type_code, encode_fn, decode_fn)
    _type_code_registry[type_code] = (cls, decode_fn)


def _is_namedtuple(cls: Type) -> bool:
    """Check if a class is a NamedTuple."""
    return (
        isinstance(cls, type)
        and issubclass(cls, tuple)
        and hasattr(cls, "_fields")
        and hasattr(cls, "_asdict")
    )


def _dataclass_encode(obj: Any) -> dict:
    """Encode a dataclass to a dict."""
    result = {}
    for field in fields(obj):
        result[field.name] = getattr(obj, field.name)
    return result


def _dataclass_decode(cls: Type, data: dict) -> Any:
    """Decode a dict to a dataclass."""
    return cls(**data)


def _namedtuple_encode(obj: Any) -> dict:
    """Encode a NamedTuple to a dict."""
    return obj._asdict()


def _namedtuple_decode(cls: Type, data: dict) -> Any:
    """Decode a dict to a NamedTuple."""
    return cls(**data)


def get_encoder(cls: Type) -> tuple[int, Callable] | None:
    """Get the type code and encoder for a class."""
    # Check exact type first
    if cls in _type_registry:
        type_code, encode_fn, _ = _type_registry[cls]
        return type_code, encode_fn

    # Check base classes
    for registered_cls, (type_code, encode_fn, _) in _type_registry.items():
        if isinstance(cls, type) and issubclass(cls, registered_cls):
            return type_code, encode_fn

    return None


def get_decoder(type_code: int) -> tuple[Type, Callable] | None:
    """Get the class and decoder for a type code."""
    return _type_code_registry.get(type_code)


def is_registered(cls: Type) -> bool:
    """Check if a type is registered."""
    if cls in _type_registry:
        return True
    for registered_cls in _type_registry:
        if isinstance(cls, type) and issubclass(cls, registered_cls):
            return True
    return False


def clear_registry() -> None:
    """Clear all registered types. Useful for testing."""
    global _next_type_code
    _type_registry.clear()
    _type_code_registry.clear()
    _next_type_code = 0x10
