"""Primitive C data types e.g. int, char."""

import builtins
import struct

from six import integer_types

from .base import DataType, Instance

from .endianness import Endianness

class Primitive(DataType):
    """Defines generic primitive data-types as supported by :py:mod:`struct`.
    
    Note that this type should only be used to define the simple non-compound
    types supported by struct. For example, this should not be used to define
    arrays, strings and pointers.
    """
    
    def __init__(self, name, struct_format, default_value,
                 cast, to_literal=repr, native=False):
        """Define a new primitive type.
        
        Parameters
        ----------
        struct_format : str
            The :py:mod:`struct` format string for the primitive type to be
            defined.
        default_value
            The default value that this type takes.
        cast : function
            A cast function which casts values into the type contained by the
            primitive.
        to_literal : function
            A function which accepts a single argument, the Python value to
            format, and returns the C literal equivilent as a string.
        """
        self.struct_format = struct_format
        self.default_value = default_value
        self.cast = cast
        self.to_literal = to_literal
        
        super(Primitive, self).__init__(name, native)
    
    def __call__(self, value=None):
        if value is None:
            value = self.default_value
        return PrimitiveInstance(self, value)


class PrimitiveInstance(Instance):
    """An instance of a primitive value.
    
    The value of the primitive is accessed via the :py:meth:`.value` accessor.
    """
    
    def __init__(self, data_type, value):
        assert isinstance(data_type, Primitive)
        super(PrimitiveInstance, self).__init__(data_type)
        self.value = value
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        self._value = self.data_type.cast(value)
        self._value_changed()
    
    @property
    def size(self):
        return struct.calcsize("<" + self.data_type.struct_format)
    
    @property
    def literal(self):
        return self.data_type.to_literal(self.value)
    
    def pack(self, endianness=Endianness.little):
        return struct.pack(endianness.value + self.data_type.struct_format,
                           self.value)
    
    def unpack(self, data, endianness=Endianness.little):
        self.value = struct.unpack(endianness.value +
                                   self.data_type.struct_format,
                                   data)[0]
    
    def __str__(self):
        return str(self.value)

def _cast_char(value):
    if isinstance(value, integer_types):
        # Convert from integer
        return bytes([value])
    else:
        # Truncate bytes to a single byte/character
        return bytes([bytes(value)[0]])

def _literal_char(value):
    """Render a character as a C literal."""
    
    int = builtins.int
    value = int(value[0])
    if value < 128:
        return "'{}'".format(repr(chr(value))[1:-1])
    else:
        return "'\\x{:02x}'".format(value)

def _cast_signed(value, n_bits):
    """Utility function: return the value cast into a signed integer with the
    specified number of bits."""
    int = builtins.int
    return (int(value) |
            (-((int(value) >> (n_bits - 1)) & 1) << n_bits))


def _cast_unsigned(value, n_bits):
    """Utility function: return the value cast as an unsigned integer with the
    specified number of bits."""
    int = builtins.int
    return int(value) & ((1 << n_bits) - 1)


char = Primitive(name="char", struct_format="c",
                 default_value=b"\0",
                 cast=_cast_char,
                 to_literal=_literal_char,
                 native=True)

signed_char = Primitive(name="signed char", struct_format="b",
                        default_value=0,
                        cast=(lambda c: _cast_signed(c, 8)),
                        native=True)

unsigned_char = Primitive(name="unsigned char", struct_format="B",
                          default_value=0,
                          cast=(lambda c: _cast_unsigned(c, 8)),
                          native=True)

_Bool = Primitive(name="_Bool", struct_format="?",
                  default_value=False,
                  cast=bool,
                  to_literal=(lambda b: "1" if b else "0"),
                  native=True)

short = Primitive(name="short", struct_format="h",
                  default_value=0,
                  cast=(lambda i: _cast_signed(i, 16)),
                  native=True)

unsigned_short = Primitive(name="unsigned short", struct_format="H",
                           default_value=0,
                           cast=(lambda i: _cast_unsigned(i, 16)),
                           native=True)

# Warning: redefines "int"
int = Primitive(name="int", struct_format="i",
                default_value=0,
                cast=(lambda i: _cast_signed(i, 32)),
                native=True)

unsigned_int = Primitive(name="unsigned int", struct_format="I",
                         default_value=0,
                         cast=(lambda i: _cast_unsigned(i, 32)),
                         native=True)

# Warning: redefines "long"
long = Primitive(name="long", struct_format="l",
                 default_value=0,
                 cast=(lambda l: _cast_signed(l, 32)),
                 native=True)

unsigned_long = Primitive(name="unsigned long", struct_format="L",
                          default_value=0,
                          cast=(lambda l: _cast_unsigned(l, 32)),
                          native=True)

long_long = Primitive(name="long long", struct_format="q",
                      default_value=0,
                      cast=(lambda ll: _cast_signed(ll, 64)),
                      native=True)

unsigned_long_long = Primitive(name="unsigned long long", struct_format="Q",
                               default_value=0,
                               cast=(lambda ll: _cast_unsigned(ll, 64)),
                               native=True)

# Warning: redefines "long"
float = Primitive(name="float", struct_format="f",
                  default_value=0.0,
                  cast=builtins.float,
                  native=True)

double = Primitive(name="double", struct_format="d",
                   default_value=0.0,
                   cast=builtins.float,
                   native=True)
