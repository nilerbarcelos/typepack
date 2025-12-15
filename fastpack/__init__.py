"""
fastpack - A fast, zero-dependency binary serialization library for Python.

Usage:
    >>> import fastpack
    >>> data = fastpack.pack({"name": "Ana", "age": 30})
    >>> obj = fastpack.unpack(data)
    >>> obj
    {'name': 'Ana', 'age': 30}

Custom types:
    >>> from dataclasses import dataclass
    >>> import fastpack
    >>>
    >>> @dataclass
    ... class User:
    ...     name: str
    ...     age: int
    >>>
    >>> user = User("Ana", 30)
    >>> data = fastpack.pack(user)
    >>> fastpack.unpack(data)
    {'__dataclass__': 'User', '__module__': '__main__', 'name': 'Ana', 'age': 30}
"""

from fastpack.core import pack, unpack
from fastpack.types import register, clear_registry

__version__ = "0.3.0"
__all__ = ["pack", "unpack", "register", "clear_registry"]
