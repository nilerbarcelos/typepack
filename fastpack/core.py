"""
Core serialization functions for fastpack.

Binary format based on MessagePack specification for interoperability.
"""

import struct
from typing import Any


# Format markers (MessagePack compatible)
_NONE = 0xC0
_FALSE = 0xC2
_TRUE = 0xC3
_BIN8 = 0xC4
_BIN16 = 0xC5
_BIN32 = 0xC6
_FLOAT32 = 0xCA
_FLOAT64 = 0xCB
_UINT8 = 0xCC
_UINT16 = 0xCD
_UINT32 = 0xCE
_UINT64 = 0xCF
_INT8 = 0xD0
_INT16 = 0xD1
_INT32 = 0xD2
_INT64 = 0xD3
_STR8 = 0xD9
_STR16 = 0xDA
_STR32 = 0xDB
_ARRAY16 = 0xDC
_ARRAY32 = 0xDD
_MAP16 = 0xDE
_MAP32 = 0xDF


def pack(obj: Any) -> bytes:
    """
    Serialize a Python object to binary format.

    Supported types:
        - None
        - bool
        - int
        - float
        - str
        - bytes
        - list
        - dict (with string keys)

    Args:
        obj: The Python object to serialize.

    Returns:
        Binary representation of the object.

    Raises:
        TypeError: If the object type is not supported.
    """
    buffer = bytearray()
    _pack_value(obj, buffer)
    return bytes(buffer)


def unpack(data: bytes) -> Any:
    """
    Deserialize binary data to a Python object.

    Args:
        data: Binary data to deserialize.

    Returns:
        The deserialized Python object.

    Raises:
        ValueError: If the data format is invalid.
    """
    result, _ = _unpack_value(data, 0)
    return result


def _pack_value(obj: Any, buffer: bytearray) -> None:
    """Pack a single value into the buffer."""
    if obj is None:
        buffer.append(_NONE)

    elif obj is True:
        buffer.append(_TRUE)

    elif obj is False:
        buffer.append(_FALSE)

    elif isinstance(obj, int):
        _pack_int(obj, buffer)

    elif isinstance(obj, float):
        _pack_float(obj, buffer)

    elif isinstance(obj, str):
        _pack_str(obj, buffer)

    elif isinstance(obj, bytes):
        _pack_bytes(obj, buffer)

    elif isinstance(obj, list):
        _pack_list(obj, buffer)

    elif isinstance(obj, dict):
        _pack_dict(obj, buffer)

    else:
        raise TypeError(f"Unsupported type: {type(obj).__name__}")


def _pack_int(value: int, buffer: bytearray) -> None:
    """Pack an integer value."""
    if 0 <= value <= 127:
        # Positive fixint
        buffer.append(value)
    elif -32 <= value < 0:
        # Negative fixint
        buffer.append(value & 0xFF)
    elif 0 <= value <= 0xFF:
        buffer.append(_UINT8)
        buffer.append(value)
    elif 0 <= value <= 0xFFFF:
        buffer.append(_UINT16)
        buffer.extend(struct.pack(">H", value))
    elif 0 <= value <= 0xFFFFFFFF:
        buffer.append(_UINT32)
        buffer.extend(struct.pack(">I", value))
    elif 0 <= value <= 0xFFFFFFFFFFFFFFFF:
        buffer.append(_UINT64)
        buffer.extend(struct.pack(">Q", value))
    elif -128 <= value < 0:
        buffer.append(_INT8)
        buffer.extend(struct.pack(">b", value))
    elif -32768 <= value < 0:
        buffer.append(_INT16)
        buffer.extend(struct.pack(">h", value))
    elif -2147483648 <= value < 0:
        buffer.append(_INT32)
        buffer.extend(struct.pack(">i", value))
    else:
        buffer.append(_INT64)
        buffer.extend(struct.pack(">q", value))


def _pack_float(value: float, buffer: bytearray) -> None:
    """Pack a float value (always as float64 for precision)."""
    buffer.append(_FLOAT64)
    buffer.extend(struct.pack(">d", value))


def _pack_str(value: str, buffer: bytearray) -> None:
    """Pack a string value."""
    encoded = value.encode("utf-8")
    length = len(encoded)

    if length <= 31:
        # Fixstr
        buffer.append(0xA0 | length)
    elif length <= 0xFF:
        buffer.append(_STR8)
        buffer.append(length)
    elif length <= 0xFFFF:
        buffer.append(_STR16)
        buffer.extend(struct.pack(">H", length))
    else:
        buffer.append(_STR32)
        buffer.extend(struct.pack(">I", length))

    buffer.extend(encoded)


def _pack_bytes(value: bytes, buffer: bytearray) -> None:
    """Pack a bytes value."""
    length = len(value)

    if length <= 0xFF:
        buffer.append(_BIN8)
        buffer.append(length)
    elif length <= 0xFFFF:
        buffer.append(_BIN16)
        buffer.extend(struct.pack(">H", length))
    else:
        buffer.append(_BIN32)
        buffer.extend(struct.pack(">I", length))

    buffer.extend(value)


def _pack_list(value: list, buffer: bytearray) -> None:
    """Pack a list value."""
    length = len(value)

    if length <= 15:
        # Fixarray
        buffer.append(0x90 | length)
    elif length <= 0xFFFF:
        buffer.append(_ARRAY16)
        buffer.extend(struct.pack(">H", length))
    else:
        buffer.append(_ARRAY32)
        buffer.extend(struct.pack(">I", length))

    for item in value:
        _pack_value(item, buffer)


def _pack_dict(value: dict, buffer: bytearray) -> None:
    """Pack a dict value."""
    length = len(value)

    if length <= 15:
        # Fixmap
        buffer.append(0x80 | length)
    elif length <= 0xFFFF:
        buffer.append(_MAP16)
        buffer.extend(struct.pack(">H", length))
    else:
        buffer.append(_MAP32)
        buffer.extend(struct.pack(">I", length))

    for k, v in value.items():
        _pack_value(k, buffer)
        _pack_value(v, buffer)


def _unpack_value(data: bytes, offset: int) -> tuple[Any, int]:
    """Unpack a single value from the data at the given offset."""
    if offset >= len(data):
        raise ValueError("Unexpected end of data")

    marker = data[offset]
    offset += 1

    # Positive fixint (0x00 - 0x7F)
    if marker <= 0x7F:
        return marker, offset

    # Fixmap (0x80 - 0x8F)
    if 0x80 <= marker <= 0x8F:
        length = marker & 0x0F
        return _unpack_map(data, offset, length)

    # Fixarray (0x90 - 0x9F)
    if 0x90 <= marker <= 0x9F:
        length = marker & 0x0F
        return _unpack_array(data, offset, length)

    # Fixstr (0xA0 - 0xBF)
    if 0xA0 <= marker <= 0xBF:
        length = marker & 0x1F
        return _unpack_str(data, offset, length)

    # Negative fixint (0xE0 - 0xFF)
    if marker >= 0xE0:
        return struct.unpack(">b", bytes([marker]))[0], offset

    # None
    if marker == _NONE:
        return None, offset

    # Boolean
    if marker == _FALSE:
        return False, offset
    if marker == _TRUE:
        return True, offset

    # Binary
    if marker == _BIN8:
        length = data[offset]
        offset += 1
        return data[offset:offset + length], offset + length
    if marker == _BIN16:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
        return data[offset:offset + length], offset + length
    if marker == _BIN32:
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        return data[offset:offset + length], offset + length

    # Float
    if marker == _FLOAT32:
        value = struct.unpack(">f", data[offset:offset + 4])[0]
        return value, offset + 4
    if marker == _FLOAT64:
        value = struct.unpack(">d", data[offset:offset + 8])[0]
        return value, offset + 8

    # Unsigned integers
    if marker == _UINT8:
        return data[offset], offset + 1
    if marker == _UINT16:
        value = struct.unpack(">H", data[offset:offset + 2])[0]
        return value, offset + 2
    if marker == _UINT32:
        value = struct.unpack(">I", data[offset:offset + 4])[0]
        return value, offset + 4
    if marker == _UINT64:
        value = struct.unpack(">Q", data[offset:offset + 8])[0]
        return value, offset + 8

    # Signed integers
    if marker == _INT8:
        value = struct.unpack(">b", data[offset:offset + 1])[0]
        return value, offset + 1
    if marker == _INT16:
        value = struct.unpack(">h", data[offset:offset + 2])[0]
        return value, offset + 2
    if marker == _INT32:
        value = struct.unpack(">i", data[offset:offset + 4])[0]
        return value, offset + 4
    if marker == _INT64:
        value = struct.unpack(">q", data[offset:offset + 8])[0]
        return value, offset + 8

    # Strings
    if marker == _STR8:
        length = data[offset]
        offset += 1
        return _unpack_str(data, offset, length)
    if marker == _STR16:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
        return _unpack_str(data, offset, length)
    if marker == _STR32:
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        return _unpack_str(data, offset, length)

    # Arrays
    if marker == _ARRAY16:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
        return _unpack_array(data, offset, length)
    if marker == _ARRAY32:
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        return _unpack_array(data, offset, length)

    # Maps
    if marker == _MAP16:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        offset += 2
        return _unpack_map(data, offset, length)
    if marker == _MAP32:
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        return _unpack_map(data, offset, length)

    raise ValueError(f"Unknown format marker: 0x{marker:02X}")


def _unpack_str(data: bytes, offset: int, length: int) -> tuple[str, int]:
    """Unpack a string value."""
    value = data[offset:offset + length].decode("utf-8")
    return value, offset + length


def _unpack_array(data: bytes, offset: int, length: int) -> tuple[list, int]:
    """Unpack an array value."""
    result = []
    for _ in range(length):
        item, offset = _unpack_value(data, offset)
        result.append(item)
    return result, offset


def _unpack_map(data: bytes, offset: int, length: int) -> tuple[dict, int]:
    """Unpack a map value."""
    result = {}
    for _ in range(length):
        key, offset = _unpack_value(data, offset)
        value, offset = _unpack_value(data, offset)
        result[key] = value
    return result, offset
