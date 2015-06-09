"""Enumeration Types."""

from collections import OrderedDict

from six import iteritems, itervalues, integer_types, next

import struct

from cdata.endianness import Endianness

from cdata.base import DataType, Instance

from cdata.primitive import Primitive, unsigned_int

from cdata.utils import indent, comment

class Enum(DataType):
    """A C enumeration type."""
    
    """Mapping from enum size to struct format character."""
    ENUM_TYPES = {
        8: "B",
        16: "H",
        32: "I",
        64: "Q",
    }
    
    def __init__(self, *members, enum_size=32, native=False, doc=""):
        """Define a new enumeration type.
        
        Parameters
        ----------
        enum_name : str
            The name of the enum. May be omitted to define an anonymous enum.
        *members : (name, value), ...
            The remaining arguments must be the names and values of each
            enumeration value. The values must be given as integers.
        enum_size : int
            The number of bits in the enumeration type (default: 32).
        """
        # Work out the format string to use to pack this enum type
        if enum_size not in self.ENUM_TYPES:
            raise ValueError(
                "{}-bit enums not supported (supported: {})".format(
                    enum_size,
                    ", ".join(map(str, self.ENUM_TYPES))))
        self._struct_format = self.ENUM_TYPES[enum_size]
        
        # Extract the name of the enum, if given
        if len(members) >= 1 and isinstance(members[0], str):
            self.enum_name = members[0]
            members = members[1:]
        else:
            self.enum_name = None
        
        # Fail if an empty enumeration is created
        if len(members) == 0:
            raise ValueError("empty enum types are not supported.")
        
        # Validate and record the members of the enumeration
        next_value = 0
        self._members = OrderedDict()
        self._member_docs = OrderedDict()
        for name_value_doc in members:
            if len(name_value_doc) == 2:
                name, value = name_value_doc
                member_doc = ""
            else:
                name, value, member_doc = name_value_doc
            # Automatically assign values to members if non given
            if value is None:
                value = next_value
            
            # Check the supplied value for validity
            if not isinstance(value, integer_types):
                raise ValueError("values must be integers (or None)")
            if name in self._members:
                raise ValueError("name '{}' defined multiple times".format(name))
            if value in itervalues(self._members):
                raise ValueError(
                    "value {} defined multiple times".format(value))
            if not 0 <= value < (1 << enum_size):
                raise ValueError("value {} is out of range".format(value))
            if name.startswith("_") or name in dir(self):
                raise ValueError("name '{}' is reserved".format(name))
            
            self._members[name] = value
            self._member_docs[name] = member_doc
            next_value = value + 1
        
        # If anonymous, the name of the type becomes its full definition.
        if self.enum_name is not None:
            name = "enum {}".format(self.enum_name)
        else:
            name = self._definition.rstrip(";")
        
        super(Enum, self).__init__(name, native, doc)
    
    def __call__(self, name=None):
        """Create an instance of an enumeration value.
        
        Note: the default value is the default value of the underlying integer
        type and thus will probably be zero.
        """
        return EnumInstance(self, name)
    
    def __getattr__(self, name):
        """Allow convenient instantiation of enum instances with particular
        values."""
        if name in self._members:
            return self(name)
        else:
            raise AttributeError(name)
    
    @property
    def prototype(self):
        if self.enum_name is not None:
            return "enum {};".format(self.enum_name)
        else:
            return ""
    
    @property
    def definition(self):
        if self.enum_name is not None:
            if self.doc:
                return "{}\n{}".format(comment(self.doc),
                                       self._definition)
            else:
                return self._definition
        else:
            return ""
    
    @property
    def _definition(self):
        """The full definition of the enum, even if it is anonymous."""
        members = []
        for name, value in iteritems(self._members):
            member = "{} = {}".format(name, value)
            
            member_doc = self._member_docs[name]
            if member_doc:
                member = "{}\n{}".format(comment(member_doc), member)
            
            members.append(member)
            
        members = ",\n".join(members)
        
        return ("enum {}{{\n"
                "{}\n"
                "}};").format("{} ".format(self.enum_name
                                           if self.enum_name is not None
                                           else "").lstrip(),
                              indent(members))

class EnumInstance(Instance):
    """An instance of an enum type."""
    
    def __init__(self, data_type, value=None):
        super(EnumInstance, self).__init__(data_type)
        
        # If no value is given, default to the first enumeration value defined.
        if value is None:
            value = next(iter(self.data_type._members))
        
        self.value = value
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, value):
        if value not in self.data_type._members:
            raise ValueError("{} is not a member of the enum".format(value))
        self._value = value
        self._value_changed()

    @property
    def size(self):
        return struct.calcsize(self.data_type._struct_format)
    
    @property
    def literal(self):
        return self.value
    
    def pack(self, endianness=Endianness.little):
        return struct.pack(endianness.value + self.data_type._struct_format,
                           self.data_type._members[self.value])
    
    def unpack(self, data, endianness=Endianness.little):
        unpacked_value = struct.unpack(
            endianness.value + self.data_type._struct_format, data)[0]
        
        for name, value in iteritems(self.data_type._members):
            if value == unpacked_value:
                # Found the unpacked value!
                self.value = name
                break
        else:
            # The unpacked value isn't defined by the enum.
            raise ValueError("value of {} is not a member of {}".format(
                unpacked_value, repr(self.data_type)))
    
    def __str__(self):
        return self.value
