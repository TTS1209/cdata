"""Exceptions raised by the cdata module."""

class PointerToUndefinedMemoryAddress(ValueError):
    """An exception riased whenever a pointer to a value is packed which hasn't
    been allocated a memory location."""
