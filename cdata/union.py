"""Allows the definition of unions."""

from six import itervalues

from cdata.endianness import Endianness

from cdata.complex_base import ComplexType, ComplexTypeInstance

class Union(ComplexType):
    """Define C-style unions."""
    
    def __init__(self, *args, endianness=Endianness.little, native=False):
        super(Union, self).__init__("union", *args, native=native)
        self.endianness = endianness
    
    
    def __call__(self, *args, **kwargs):
        return UnionInstance(self, *args, **kwargs)


class UnionInstance(ComplexTypeInstance):
    """An instance of a union type."""
    
    def __init__(self, data_type, *args, **kwargs):
        # If more than one initialiser is given, fail since there is no
        # straight-forward way to select which one wins. (Note that nested
        # initialisers must still be allowed!)
        kwargs_names = set()
        for name in kwargs:
            kwargs_names.add(name.partition("__")[0])
        num_kwargs = len(kwargs_names)
        num_args = len(args)
        if num_args + num_kwargs > 1:
            raise ValueError("At most one union member may be initialised.")
        
        # If this flag is set, all calls to _child_value_changed are ignored.
        # This is required since when the union is changed all members of the
        # struct must be overwritten. Initially disabled while initialisation
        # takes place.
        self._ignore_child_value_changed = True
        
        super(UnionInstance, self).__init__(data_type, *args, **kwargs)
        
        # Re-enable child value change updates now the union has been
        # initialised.
        self._ignore_child_value_changed = False
        
        # Ensure consistent initial addresses
        self.address = None
        
        # Ensure consistent initial value by making it look like the member
        # specified for initialisation got assigned. Otherwise, just run through
        # the pack/unpack cycle to make everything the same in an arbitrary
        # manner. (Note there can be at most one arg/kwarg.)
        if kwargs_names:
            self._child_value_changed(
                self._member_instances[list(kwargs_names)[0]])
        elif args:
            self._child_value_changed(
                getattr(self, list(self._member_instances)[0]))
        else:
            self.unpack(self.pack(self.data_type.endianness),
                        self.data_type.endianness)
    
    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, address):
        self._address = address
        
        # Must also update the addresses of all the union members
        for instance in itervalues(self._member_instances):
            # During initialisation this setter will be called and at that point
            # in time the instance will not have been assigned so we should just
            # skip it.
            if instance is None:
                continue
            
            instance.address = address
        
        self._address_changed()
    
    @property
    def size(self):
        return max(i.size for i in itervalues(self._member_instances))
    
    def pack(self, endianness=Endianness.little):
        # Must be using the same Endianness defined when the union was defined.
        if endianness != self.data_type.endianness:
            raise ValueError(
                "Cannot pack {} defined as {}-endian, as {}-endian".format(
                    repr(self),
                    self.data_type.endianness.name,
                    endianness.name))
        
        # Returns the packed form of an arbitrary maximally-sized member.
        # XXX: This makes the assumption that a member never throws away any
        # information it unpacks which *should* be a good assumption but isn't
        # enforced...
        _, instance = max((i.size, i)
                          for i in itervalues(self._member_instances))
        return instance.pack(endianness)
    
    def unpack(self, data, endianness=Endianness.little):
        # Must be using the same Endianness defined when the union was defined.
        if endianness != self.data_type.endianness:
            raise ValueError(
                "Cannot unpack {} defined as {}-endian, as {}-endian".format(
                    repr(self),
                    self.data_type.endianness.name,
                    endianness.name))
        
        for instance in itervalues(self._member_instances):
            # Unpack the same data (or a subset thereof) into each member.
            instance.unpack(data[:instance.size], endianness)
    
    def _child_address_changed(self, child):
        """Throw a ValueError if any child's address is changed inconsistently
        with the union's address (after reverting the address to its previous
        value)."""
        if child.address != self.address:
            child.address = self.address
            raise ValueError("The address of {} is defined by its "
                             "containing union, {}, as {}".format(
                                 repr(child), repr(self), self.address))
    
    def _child_value_changed(self, child):
        """If a member's value changes, all other members must be updated
        accordingly.
        
        In order to prevent uncontrolled recursion, all value-changed callbacks
        are ignored while this function is called.
        """
        if self._ignore_child_value_changed:
            return
        self._ignore_child_value_changed = True
        try:
            # Update the current packed value with the new contents
            packed_value = bytearray(self.pack(self.data_type.endianness))
            packed_value[:child.size] = child.pack(self.data_type.endianness)
            
            # Now unpack that into all children
            self.unpack(packed_value, self.data_type.endianness)
            
            # Finally, report that the union's value was changed
            self._value_changed()
        finally:
            self._ignore_child_value_changed = False
    
    def _set_member(self, member, instance):
        super(UnionInstance, self)._set_member(member, instance)
        
        # Fix the address and update the union's value
        instance.address = self.address
        self._child_value_changed(instance)
