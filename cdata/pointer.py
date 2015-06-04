"""Allow definition of C pointers to existing types."""

import struct

from six import integer_types

from cdata.base import DataType, Instance

from cdata.endianness import Endianness

from .exceptions import PointerToUndefinedMemoryAddress

class Pointer(DataType):
    """Creates a pointer to the supplied type."""
    
    """Mapping from pointer size to struct format character."""
    POINTER_TYPES = {
        8: "B",
        16: "H",
        32: "I",
        64: "Q",
    }
    
    def __init__(self, base_type, pointer_size=32):
        """Define a pointer type.
        
        Parameters
        ----------
        base_type : :py:class:`.DataType`
            The type of value the pointer will point at.
        pointer_size : int
            The number of bits in the pointer address. Default: 32.
        """
        self.base_type = base_type
        
        # Check the pointer size is supported
        self._struct_format = Pointer.POINTER_TYPES.get(
            pointer_size, None)
        if self._struct_format is None:
            raise ValueError(
                "{}-bit pointers not supported (supported: {})".format(
                    pointer_size,
                    ", ".join(map(str, Pointer.POINTER_TYPES))))
        
        super(Pointer, self).__init__("{}*".format(self.base_type.name),
                                      base_type.native)
    
    def __call__(self, *args, **kwargs):
        return PointerInstance(self, *args, **kwargs)
    
    def iter_types(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        if self.name not in _generated:
            _generated.add(self.name)
            
            # Generate the types this pointer points at
            for t in self.base_type.iter_types(_generated):
                yield t
            
            # Now generate the pointer type itself
            yield self


class PointerInstance(Instance):
    """An pointer instance which points to exactly one instance or None if a
    void pointer.
    
    The pointer can be dereferenced via :py:meth:`.deref` which may be None if
    the pointer is NULL.
    
    The address the pointer points at can be accessed via :py:meth:`.value`. If
    this address is changed, the dereferenced instance will be replaced with a
    new (default) instance. Note: changing the address of the dereferenced value
    directly will not cause the instance to be replaced.
    """
    
    def __init__(self, data_type, value_or_address=None):
        super(PointerInstance, self).__init__(data_type)
        
        self._deref = None
        
        if isinstance(value_or_address, integer_types):
            self.value = value_or_address
        else:
            # Got a value to be dereferenced (or None)
            self.deref = value_or_address
    
    
    @property
    def deref(self):
        """Get the instance pointed to by the pointer."""
        return self._deref
    
    
    @deref.setter
    def deref(self, value):
        """Set the target of this pointer to an appropriate Instance or None to
        set the pointer to NULL.
        
        Raises
        ------
        TypeError
            If the type of instance provided is not the type supported by this
            pointer.
        """
        if value is None:
            # Set to NULL pointer
            self._deref = None
        elif hasattr(value, "data_type") and (value.data_type ==
                                              self.data_type.base_type):
            # The value is of the correct type, keep it
            self._deref = value
        else:
            # The value is not of an appropriate type. Fail.
            raise TypeError("pointer is for type {} but got {}".format(
                repr(self.data_type.base_type), repr(value)))
    
    @property
    def value(self):
        """Get the address this pointer points at."""
        if self.deref is None:
            return 0
        else:
            return self.deref.address
    
    @value.setter
    def value(self, address):
        """Change the address that this pointer points at.
        
        If changed to 0, NULL out the pointer.
        
        The pointer address changes create a new (default) instance of the
        referenced type and set its address field to the address supplied.
        
        If the address has not changed, keep the old instance.
        """
        if address == 0:
            # Passed a NULL address
            self.deref = None
        else:
            # Got an address, if changed, create a new value of that type and
            # assign it the supplied address. If unchanged, keep the existing
            # value.
            if self.deref is None or self.deref.address != address:
                self.deref = self.data_type.base_type()
                self.deref.address = address
    
    @property
    def size(self):
        return struct.calcsize("<" + self.data_type._struct_format)
    
    @property
    def literal(self):
        if self.deref is None:
            return "NULL"
        else:
            return "&{}".format(self.deref.literal)
    
    def pack(self, endianness=Endianness.little):
        if self.deref is None:
            address = 0
        elif self.deref.address is not None:
            address = self.deref.address
        else:
            raise PointerToUndefinedMemoryAddress(self.deref)
        
        return struct.pack(
            endianness.value + self.data_type._struct_format, address)
    
    def unpack(self, data, endianness=Endianness.little):
        address = struct.unpack(
            endianness.value + self.data_type._struct_format, data)[0]
        self.value = address
    
    def __str__(self):
        if self.deref is None:
            return "NULL"
        else:
            return str(self.deref)

    def iter_references(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        # This instance references the value being pointed at (unless NULL).
        if self not in _generated and self.deref is not None:
            yield self.deref
            
            for ref in self.deref.iter_references(_generated):
                yield ref
