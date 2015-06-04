"""Endianness enumeration type."""

from enum import Enum


class Endianness(Enum):
    """Primitive type endianness options."""
    little = "<"
    big = ">"
