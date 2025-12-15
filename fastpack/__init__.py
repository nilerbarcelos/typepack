"""
fastpack - A fast, zero-dependency binary serialization library for Python.

Usage:
    >>> import fastpack
    >>> data = fastpack.pack({"name": "Ana", "age": 30})
    >>> obj = fastpack.unpack(data)
    >>> obj
    {'name': 'Ana', 'age': 30}
"""

from fastpack.core import pack, unpack

__version__ = "0.1.0"
__all__ = ["pack", "unpack"]
