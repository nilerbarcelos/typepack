"""
Core serialization functions for fastpack.

Binary format based on MessagePack specification for interoperability.
"""

import struct
from dataclasses import is_dataclass, fields
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Type
from uuid import UUID

from fastpack import types as _types


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

# Extension format markers
_FIXEXT1 = 0xD4
_FIXEXT2 = 0xD5
_FIXEXT4 = 0xD6
_FIXEXT8 = 0xD7
_FIXEXT16 = 0xD8
_EXT8 = 0xC7
_EXT16 = 0xC8
_EXT32 = 0xC9

# Custom extension type codes (built-in)
_EXT_DATETIME = 0x01
_EXT_DATE = 0x02
_EXT_TIME = 0x03
_EXT_TIMEDELTA = 0x04
_EXT_DECIMAL = 0x05
_EXT_UUID = 0x06
_EXT_SET = 0x07
_EXT_TUPLE = 0x08
_EXT_FROZENSET = 0x09
_EXT_ENUM = 0x0A
_EXT_DATACLASS = 0x0B
_EXT_NAMEDTUPLE = 0x0C
_EXT_CUSTOM = 0x0D  # For registered custom types


def pack(obj: Any) -> bytes:
    """
    Serialize a Python object to binary format.

    Supported types:
        - None, bool, int, float, str, bytes
        - list, dict, tuple, set, frozenset
        - datetime, date, time, timedelta
        - Decimal, UUID
        - Enum

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

    elif isinstance(obj, Enum):
        _pack_enum(obj, buffer)

    elif isinstance(obj, int):
        _pack_int(obj, buffer)

    elif isinstance(obj, float):
        _pack_float(obj, buffer)

    elif isinstance(obj, str):
        _pack_str(obj, buffer)

    elif isinstance(obj, bytes):
        _pack_bytes(obj, buffer)

    elif isinstance(obj, datetime):
        _pack_datetime(obj, buffer)

    elif isinstance(obj, date):
        _pack_date(obj, buffer)

    elif isinstance(obj, time):
        _pack_time(obj, buffer)

    elif isinstance(obj, timedelta):
        _pack_timedelta(obj, buffer)

    elif isinstance(obj, Decimal):
        _pack_decimal(obj, buffer)

    elif isinstance(obj, UUID):
        _pack_uuid(obj, buffer)

    elif _types.is_registered(type(obj)):
        # Registered types take priority over built-in handling
        _pack_registered(obj, buffer)

    elif _is_namedtuple(obj):
        _pack_namedtuple(obj, buffer)

    elif isinstance(obj, tuple):
        _pack_tuple(obj, buffer)

    elif isinstance(obj, frozenset):
        _pack_frozenset(obj, buffer)

    elif isinstance(obj, set):
        _pack_set(obj, buffer)

    elif isinstance(obj, list):
        _pack_list(obj, buffer)

    elif isinstance(obj, dict):
        _pack_dict(obj, buffer)

    elif is_dataclass(obj) and not isinstance(obj, type):
        _pack_dataclass(obj, buffer)

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


def _pack_ext(type_code: int, data: bytes, buffer: bytearray) -> None:
    """Pack an extension type value."""
    length = len(data)

    if length == 1:
        buffer.append(_FIXEXT1)
        buffer.append(type_code)
    elif length == 2:
        buffer.append(_FIXEXT2)
        buffer.append(type_code)
    elif length == 4:
        buffer.append(_FIXEXT4)
        buffer.append(type_code)
    elif length == 8:
        buffer.append(_FIXEXT8)
        buffer.append(type_code)
    elif length == 16:
        buffer.append(_FIXEXT16)
        buffer.append(type_code)
    elif length <= 0xFF:
        buffer.append(_EXT8)
        buffer.append(length)
        buffer.append(type_code)
    elif length <= 0xFFFF:
        buffer.append(_EXT16)
        buffer.extend(struct.pack(">H", length))
        buffer.append(type_code)
    else:
        buffer.append(_EXT32)
        buffer.extend(struct.pack(">I", length))
        buffer.append(type_code)

    buffer.extend(data)


def _pack_datetime(value: datetime, buffer: bytearray) -> None:
    """Pack a datetime value as ISO format string."""
    data = value.isoformat().encode("utf-8")
    _pack_ext(_EXT_DATETIME, data, buffer)


def _pack_date(value: date, buffer: bytearray) -> None:
    """Pack a date value as ISO format string."""
    data = value.isoformat().encode("utf-8")
    _pack_ext(_EXT_DATE, data, buffer)


def _pack_time(value: time, buffer: bytearray) -> None:
    """Pack a time value as ISO format string."""
    data = value.isoformat().encode("utf-8")
    _pack_ext(_EXT_TIME, data, buffer)


def _pack_timedelta(value: timedelta, buffer: bytearray) -> None:
    """Pack a timedelta value as total seconds (float)."""
    data = struct.pack(">d", value.total_seconds())
    _pack_ext(_EXT_TIMEDELTA, data, buffer)


def _pack_decimal(value: Decimal, buffer: bytearray) -> None:
    """Pack a Decimal value as string."""
    data = str(value).encode("utf-8")
    _pack_ext(_EXT_DECIMAL, data, buffer)


def _pack_uuid(value: UUID, buffer: bytearray) -> None:
    """Pack a UUID value as 16 bytes."""
    _pack_ext(_EXT_UUID, value.bytes, buffer)


def _pack_set(value: set, buffer: bytearray) -> None:
    """Pack a set value as an array."""
    items_buffer = bytearray()
    _pack_list(list(value), items_buffer)
    _pack_ext(_EXT_SET, bytes(items_buffer), buffer)


def _pack_tuple(value: tuple, buffer: bytearray) -> None:
    """Pack a tuple value as an array."""
    items_buffer = bytearray()
    _pack_list(list(value), items_buffer)
    _pack_ext(_EXT_TUPLE, bytes(items_buffer), buffer)


def _pack_frozenset(value: frozenset, buffer: bytearray) -> None:
    """Pack a frozenset value as an array."""
    items_buffer = bytearray()
    _pack_list(list(value), items_buffer)
    _pack_ext(_EXT_FROZENSET, bytes(items_buffer), buffer)


def _pack_enum(value: Enum, buffer: bytearray) -> None:
    """Pack an Enum value as [module, class, name, value]."""
    enum_data = {
        "module": type(value).__module__,
        "class": type(value).__name__,
        "name": value.name,
        "value": value.value,
    }
    items_buffer = bytearray()
    _pack_dict(enum_data, items_buffer)
    _pack_ext(_EXT_ENUM, bytes(items_buffer), buffer)


def _is_namedtuple(obj: Any) -> bool:
    """Check if an object is a NamedTuple instance."""
    return (
        isinstance(obj, tuple)
        and hasattr(type(obj), "_fields")
        and hasattr(type(obj), "_asdict")
    )


def _pack_namedtuple(value: Any, buffer: bytearray) -> None:
    """Pack a NamedTuple as {__namedtuple__: class_name, **fields}."""
    data = {
        "__namedtuple__": type(value).__name__,
        "__module__": type(value).__module__,
        **value._asdict(),
    }
    items_buffer = bytearray()
    _pack_dict(data, items_buffer)
    _pack_ext(_EXT_NAMEDTUPLE, bytes(items_buffer), buffer)


def _pack_dataclass(value: Any, buffer: bytearray) -> None:
    """Pack a dataclass as {__dataclass__: class_name, **fields}."""
    data = {
        "__dataclass__": type(value).__name__,
        "__module__": type(value).__module__,
    }
    for field in fields(value):
        data[field.name] = getattr(value, field.name)

    items_buffer = bytearray()
    _pack_dict(data, items_buffer)
    _pack_ext(_EXT_DATACLASS, bytes(items_buffer), buffer)


def _pack_registered(value: Any, buffer: bytearray) -> None:
    """Pack a registered custom type."""
    encoder_info = _types.get_encoder(type(value))
    if encoder_info is None:
        raise TypeError(f"Type {type(value).__name__} is not registered")

    type_code, encode_fn = encoder_info
    encoded_data = encode_fn(value)

    # Pack the encoded data as a dict with type info
    data = {
        "__custom__": type(value).__name__,
        "__module__": type(value).__module__,
        "__type_code__": type_code,
        "data": encoded_data,
    }
    items_buffer = bytearray()
    _pack_dict(data, items_buffer)
    _pack_ext(_EXT_CUSTOM, bytes(items_buffer), buffer)


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

    # Extension types (fixext)
    if marker == _FIXEXT1:
        type_code = data[offset]
        offset += 1
        return _unpack_ext(type_code, data[offset:offset + 1]), offset + 1
    if marker == _FIXEXT2:
        type_code = data[offset]
        offset += 1
        return _unpack_ext(type_code, data[offset:offset + 2]), offset + 2
    if marker == _FIXEXT4:
        type_code = data[offset]
        offset += 1
        return _unpack_ext(type_code, data[offset:offset + 4]), offset + 4
    if marker == _FIXEXT8:
        type_code = data[offset]
        offset += 1
        return _unpack_ext(type_code, data[offset:offset + 8]), offset + 8
    if marker == _FIXEXT16:
        type_code = data[offset]
        offset += 1
        return _unpack_ext(type_code, data[offset:offset + 16]), offset + 16

    # Extension types (ext8/16/32)
    if marker == _EXT8:
        length = data[offset]
        type_code = data[offset + 1]
        offset += 2
        return _unpack_ext(type_code, data[offset:offset + length]), offset + length
    if marker == _EXT16:
        length = struct.unpack(">H", data[offset:offset + 2])[0]
        type_code = data[offset + 2]
        offset += 3
        return _unpack_ext(type_code, data[offset:offset + length]), offset + length
    if marker == _EXT32:
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        type_code = data[offset + 4]
        offset += 5
        return _unpack_ext(type_code, data[offset:offset + length]), offset + length

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


def _unpack_ext(type_code: int, data: bytes) -> Any:
    """Unpack an extension type value."""
    if type_code == _EXT_DATETIME:
        return datetime.fromisoformat(data.decode("utf-8"))

    if type_code == _EXT_DATE:
        return date.fromisoformat(data.decode("utf-8"))

    if type_code == _EXT_TIME:
        return time.fromisoformat(data.decode("utf-8"))

    if type_code == _EXT_TIMEDELTA:
        seconds = struct.unpack(">d", data)[0]
        return timedelta(seconds=seconds)

    if type_code == _EXT_DECIMAL:
        return Decimal(data.decode("utf-8"))

    if type_code == _EXT_UUID:
        return UUID(bytes=data)

    if type_code == _EXT_SET:
        items, _ = _unpack_value(data, 0)
        return set(items)

    if type_code == _EXT_TUPLE:
        items, _ = _unpack_value(data, 0)
        return tuple(items)

    if type_code == _EXT_FROZENSET:
        items, _ = _unpack_value(data, 0)
        return frozenset(items)

    if type_code == _EXT_ENUM:
        enum_data, _ = _unpack_value(data, 0)
        # Return as dict with enum info (cannot reconstruct without class)
        return {
            "__enum__": True,
            "module": enum_data["module"],
            "class": enum_data["class"],
            "name": enum_data["name"],
            "value": enum_data["value"],
        }

    if type_code == _EXT_DATACLASS:
        dc_data, _ = _unpack_value(data, 0)
        # Return as dict with dataclass info (cannot reconstruct without class)
        return {
            "__dataclass__": dc_data.pop("__dataclass__"),
            "__module__": dc_data.pop("__module__"),
            **dc_data,
        }

    if type_code == _EXT_NAMEDTUPLE:
        nt_data, _ = _unpack_value(data, 0)
        # Return as dict with namedtuple info (cannot reconstruct without class)
        return {
            "__namedtuple__": nt_data.pop("__namedtuple__"),
            "__module__": nt_data.pop("__module__"),
            **nt_data,
        }

    if type_code == _EXT_CUSTOM:
        custom_data, _ = _unpack_value(data, 0)
        registered_type_code = custom_data["__type_code__"]

        # Try to decode using registered decoder
        decoder_info = _types.get_decoder(registered_type_code)
        if decoder_info is not None:
            _, decode_fn = decoder_info
            return decode_fn(custom_data["data"])

        # Return as dict if decoder not found
        return {
            "__custom__": custom_data["__custom__"],
            "__module__": custom_data["__module__"],
            "data": custom_data["data"],
        }

    raise ValueError(f"Unknown extension type: {type_code}")
