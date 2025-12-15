# fastpack

A fast, zero-dependency binary serialization library for Python.

## Why?

Binary serialization in Python has trade-offs:

| Library | Issue |
|---------|-------|
| **pickle** | Insecure, Python-only |
| **json** | Slow, verbose, limited types |
| **msgpack** | Requires C extension, limited Python type support |
| **protobuf** | Schema required, complex setup |

**fastpack** is designed to be:
- Zero dependencies (uses only stdlib)
- Safe (no arbitrary code execution)
- Fast (compact binary format)
- Python-friendly (native type support)

## Installation

```bash
pip install fastpack
```

## Usage

```python
import fastpack

# Serialize
data = fastpack.pack({"name": "Ana", "age": 30, "active": True})

# Deserialize
obj = fastpack.unpack(data)
print(obj)  # {'name': 'Ana', 'age': 30, 'active': True}
```

### Supported types

| Type | Example |
|------|---------|
| `None` | `None` |
| `bool` | `True`, `False` |
| `int` | `-2^63` to `2^64-1` |
| `float` | IEEE 754 double |
| `str` | `"hello"` (UTF-8) |
| `bytes` | `b"\x00\x01"` |
| `list` | `[1, 2, 3]` |
| `dict` | `{"key": "value"}` |

### Nested structures

```python
import fastpack

user = {
    "id": 123,
    "name": "Ana",
    "emails": ["ana@work.com", "ana@home.com"],
    "settings": {
        "theme": "dark",
        "notifications": True
    }
}

data = fastpack.pack(user)
restored = fastpack.unpack(data)

assert user == restored
```

## Size comparison

fastpack produces smaller output than JSON:

```python
import json
import fastpack

obj = {"name": "Ana", "age": 30, "active": True}

json_size = len(json.dumps(obj).encode())  # 42 bytes
pack_size = len(fastpack.pack(obj))        # 27 bytes

print(f"JSON: {json_size} bytes")
print(f"fastpack: {pack_size} bytes")
print(f"Reduction: {100 - (pack_size/json_size*100):.0f}%")
# JSON: 42 bytes
# fastpack: 27 bytes
# Reduction: 36%
```

## Binary format

fastpack uses a MessagePack-compatible binary format for interoperability.

| Type | Format |
|------|--------|
| fixint | `0x00` - `0x7F` (0-127) |
| fixmap | `0x80` - `0x8F` (0-15 elements) |
| fixarray | `0x90` - `0x9F` (0-15 elements) |
| fixstr | `0xA0` - `0xBF` (0-31 bytes) |
| nil | `0xC0` |
| false | `0xC2` |
| true | `0xC3` |
| float64 | `0xCB` + 8 bytes |
| uint/int | `0xCC` - `0xD3` + 1-8 bytes |
| str | `0xD9` - `0xDB` + length + data |
| array | `0xDC` - `0xDD` + length + items |
| map | `0xDE` - `0xDF` + length + pairs |

## Development

```bash
# Clone the repository
git clone https://github.com/nilerbarcelos/fastpack.git
cd fastpack

# Install dev dependencies
pip install hatch

# Run tests
hatch run test:run
```

## Roadmap

### v0.1.0 — MVP (current)
- Basic types: int, float, str, bytes, bool, None, list, dict
- pack/unpack API
- Zero dependencies

### v0.2.0 — Python types
- datetime, date, time, timedelta
- Decimal, UUID
- set, tuple, frozenset
- Enum support

### v0.3.0 — Extensibility
- `@fastpack.register` for custom types
- Native dataclass support
- Native Pydantic support

### v0.4.0 — Streaming
- `pack_stream` / `unpack_stream`
- File-like object support
- Async support

## License

MIT
