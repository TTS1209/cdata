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
        # This will cause any child instances to have their addresses reset
        self.address = None
    
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
        
        # Notify any containers
        self._address_changed()
    
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
    
    def _child_address_changed(self, child):
        """When a child's address is changed, thrown an exception if it is
        inconsistent (after changing it back)."""
        address = self.address
        
        # Find the child member in the struct (while calculating the appropriate
        # address along the way)
        for instance in itervalues(self._member_instances):
            if instance is child:
                if instance.address != address:
                    # Fix the address before throwing the exception
                    instance.address = address
                    raise ValueError("The address of {} is defined by its "
                                     "containing struct, {}, as {}".format(
                                         repr(child), repr(self), address))
                else:
                    # The child's address is consistent with what it should be
                    return
            
            # Note that the address may be None in which case it can't be
            # incremented.
            if address is not None:
                address += instance.size
        
        # If we got here, the child was not a member of the struct which means
        # there has been a bug somewhere.
        assert False, (  # pragma: no cover
            "Child is not a member of this struct. This is a bug.")
    
    def _set_member(self, name, instance):
        super(StructInstance, self)._set_member(name, instance)
        
        # Re-compute all addresses in order to assign an address to this member
        self.address = self.address
