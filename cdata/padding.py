"""A simple padding type."""

import builtins
import struct

from six import integer_types

from cdata.base import DataType, Instance

from cdata.endianness import Endianness

from cdata.utils import char_literal

class Padding(DataType):
    """Defines a type which acts as a padding value.
    
    A padding value (importantly) remembers any value unpacked into it and
    returns that value when packed. By default they pack into null bytes.
    """
    
    def __init__(self, length):
        """Define a new padding value type which pads the specified number of
        bytes.
        
        Parameters
        ----------
        length : int
            Number of bytes to pad
        """
        self.length = length
        
        name = self.declare()
        
        # The padding type just uses arrays of chars and thus is completely
        # native.
        super(Padding, self).__init__(name, True)
    
    def __call__(self):
        return PaddingInstance(self)
    
    def declare(self, identifier=""):
        return "char{}[{}]".format(" {}".format(identifier).rstrip(),
                                   self.length)

class PaddingInstance(Instance):
    """An instance of a padding value."""
    
    def __init__(self, data_type):
        assert isinstance(data_type, Padding)
        super(PaddingInstance, self).__init__(data_type)
        
        # The internal buffer where the padding values are stored, initially
        # null bytes.
        self._bytes = bytearray([0] * self.data_type.length)
    
    @property
    def size(self):
        return self.data_type.length
    
    @property
    def literal(self):
        length = self.data_type.length
        return "{{{}}}".format(", ".join(char_literal(bytes([b]))
                               for b in self._bytes))
    
    def pack(self, endianness=Endianness.little):
        return bytes(self._bytes)
    
    def unpack(self, data, endianness=Endianness.little):
        self._bytes[:] = data
        
        # Not entirely meaningful, but honest.
        self._value_changed()
    
    def __str__(self):
        return str(bytes(self._bytes))
