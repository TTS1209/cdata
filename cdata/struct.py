"""Allows the definition of structs."""

from six import itervalues

from cdata.endianness import Endianness

from cdata.complex_base import ComplexType, ComplexTypeInstance

class Struct(ComplexType):
    """Define C-style structs."""
    
    def __init__(self, *args, native=False):
        super(Struct, self).__init__("struct", *args, native=native)
    
    
    def __call__(self, *args, **kwargs):
        return StructInstance(self, *args, **kwargs)


class StructInstance(ComplexTypeInstance):
    """An instance of a struct type."""
    
    def __init__(self, *args, **kwargs):
        super(StructInstance, self).__init__(*args, **kwargs)
    
    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, address):
        self._address = address
        
        # Must also update the addresses of all the struct members
        for instance in itervalues(self._member_instances):
            # During initialisation this setter will be called and at that point
            # in time the instance will not have been assigned so we should just
            # skip it.
            if instance is None:
                continue
            
            instance.address = address
            
            # The address may have been changed to None
            if address is not None:
                address += instance.size
    
    @property
    def size(self):
        return sum(i.size for i in itervalues(self._member_instances))
    
    def pack(self, endianness=Endianness.little):
        # Just concatenate all the fields (without any padding bytes) to get the
        # total struct size
        return b"".join(i.pack(endianness)
                        for i in itervalues(self._member_instances))
    
    def unpack(self, data, endianness=Endianness.little):
        for instance in itervalues(self._member_instances):
            this_data, data = data[:instance.size], data[instance.size:]
            instance.unpack(this_data, endianness)
