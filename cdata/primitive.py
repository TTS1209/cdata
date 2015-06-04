"""Primitive C data types e.g. int, char."""

import builtins
import struct

from .base import DataType, Instance

from .endianness import Endianness

class Primitive(DataType):
    """Defines generic primitive data-types as supported by :py:mod:`struct`.
    
    Note that this type should only be used to define the simple non-compound
    types supported by struct. For example, this should not be used to define
    arrays, strings and pointers.
    """
    
    def __init__(self, name, struct_format, default_value,
                 to_literal=repr, native=False):
        """Define a new primitive type.
        
        Parameters
        ----------
        struct_format : str
            The :py:mod:`struct` format string for the primitive type to be
            defined.
        default_value
            The default value that this type takes.
        to_literal : function
            A function which accepts a single argument, the Python value to
            format, and returns the C literal equivilent as a string.
        """
        self.struct_format = struct_format
        self.default_value = default_value
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
        self.value = value
        super(PrimitiveInstance, self).__init__(data_type)
    
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

def _literal_char(value):
    """Render a character as a C literal."""
    
    int = builtins.int
    value = int(value[0])
    if value < 128:
        return "'{}'".format(repr(chr(value))[1:-1])
    else:
        return "'\\x{:02x}'".format(value)

def _literal_signed(value, n_bits):
    """Utility function: renders the given integer value as a C literal signed
    integer with the supplied number of bits."""
    int = builtins.int
    return str(int(value) |
               (-((int(value) >> (n_bits - 1)) & 1) << n_bits))


def _literal_unsigned(value, n_bits):
    """Utility function: renders the given integer value as a C literal unsigned
    integer with the supplied number of bits."""
    int = builtins.int
    return str(int(value) & ((1 << n_bits) - 1))


char = Primitive(name="char", struct_format="c",
                 default_value=b"\0",
                 to_literal=_literal_char,
                 native=True)

signed_char = Primitive(name="signed char", struct_format="b",
                        default_value=0,
                        to_literal=(lambda c: _literal_signed(c, 8)),
                        native=True)

unsigned_char = Primitive(name="unsigned char", struct_format="B",
                          default_value=0,
                          to_literal=(lambda c: _literal_unsigned(c, 8)),
                          native=True)

_Bool = Primitive(name="_Bool", struct_format="?",
                  default_value=False,
                  to_literal=(lambda b: "1" if b else "0"),
                  native=True)

short = Primitive(name="short", struct_format="h",
                  default_value=0,
                  to_literal=(lambda i: _literal_signed(i, 16)),
                  native=True)

unsigned_short = Primitive(name="unsigned short", struct_format="H",
                           default_value=0,
                           to_literal=(lambda i: _literal_unsigned(i, 16)),
                           native=True)

# Warning: redefines "int"
int = Primitive(name="int", struct_format="i",
                default_value=0,
                to_literal=(lambda i: _literal_signed(i, 32)),
                native=True)

unsigned_int = Primitive(name="unsigned int", struct_format="I",
                         default_value=0,
                         to_literal=(lambda i: _literal_unsigned(i, 32)),
                         native=True)

# Warning: redefines "long"
long = Primitive(name="long", struct_format="l",
                 default_value=0,
                 to_literal=(lambda l: _literal_signed(l, 32)),
                 native=True)

unsigned_long = Primitive(name="unsigned long", struct_format="L",
                          default_value=0,
                          to_literal=(lambda l: _literal_unsigned(l, 32)),
                          native=True)

long_long = Primitive(name="long long", struct_format="q",
                      default_value=0,
                      to_literal=(lambda ll: _literal_signed(ll, 64)),
                      native=True)

unsigned_long_long = Primitive(name="unsigned long long", struct_format="Q",
                               default_value=0,
                               to_literal=(lambda ll:
                                           _literal_unsigned(ll, 64)),
                               native=True)

# Warning: redefines "long"
float = Primitive(name="float", struct_format="f",
                  default_value=0.0,
                  to_literal=(lambda f: repr(builtins.float(f))),
                  native=True)

double = Primitive(name="double", struct_format="d",
                   default_value=0.0,
                   to_literal=(lambda f: repr(builtins.float(f))),
                   native=True)
