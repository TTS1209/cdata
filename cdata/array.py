"""An array type."""

from six import integer_types

from cdata.base import DataType, Instance

from cdata.endianness import Endianness

from cdata.primitive import Primitive

class Array(DataType):
    """Defines an array of a particular type.
    
    This type defines actual arrays, i.e. contiguous blocks of memory with a
    sequence of slots for entries of various types. Specifically, it *isn't*
    just a pointer to the head of an array (though one can, of course, create
    such a pointer).
    """
    
    def __init__(self, base_type, length, doc=""):
        """Define a new array of the specified data type and length.
        
        Parameters
        ----------
        base_type : :py:class:`.DataType`
            The data type that this array holds.
        length : int
            Number of entries in the array.
        """
        self.base_type = base_type
        self.length = length
        
        name = self.declare()
        
        # Arrays are native since they're a basic part of the language.
        super(Array, self).__init__(name, True, doc)
    
    def __call__(self, values=[]):
        return ArrayInstance(self, values)
    
    def declare(self, identifier=""):
        return "{}[{}]".format(self.base_type.declare(identifier), self.length)
    
    def iter_types(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        if self.name not in _generated:
            _generated.add(self.name)
            
            for t in self.base_type.iter_types(_generated):
                yield t
            
            yield self

class ArrayInstance(Instance):
    """An instance of an array."""
    
    def __init__(self, data_type, values=[]):
        assert isinstance(data_type, Array)
        
        # Used to suppress value changed notifications while unpacking the array
        self._ignore_child_value_changed = False
        
        # The internal array of instances, one for each array element.
        self._instances = [None] * data_type.length
        
        super(ArrayInstance, self).__init__(data_type)
        
        # Make sure not too many default values are provided
        if len(values) > self.data_type.length:
            raise ValueError("too many ({}) values supplied for {}-entry array.".format(
                len(values), self.data_type.length))
        
        # Add the supplied default values
        for i, instance in enumerate(values):
            self[i] = instance
        
        # Initialise the others with defaults
        for i in range(len(values), self.data_type.length):
            self[i] = self.data_type.base_type()
    
    
    @property
    def address(self):
        return self._address
    
    @address.setter
    def address(self, address):
        self._address = address
        
        # Update all instance addresses
        for instance in self:
            # During initialisation not all instances will have a value so
            # simply terminate.
            if instance is None:
                break
            
            instance.address = address
            if address is not None:
                address += instance.size
        
        self._address_changed()
    
    def __len__(self):
        return self.data_type.length
    
    def __iter__(self):
        return iter(self._instances)
    
    def __getitem__(self, key):
        """Get the instance at a particular position in the array."""
        # Check in range
        if key >= len(self) or key < -len(self):
            raise IndexError("array index {} out of range".format(key))
        
        return self._instances[key]
    
    def __setitem__(self, key, instance):
        """Set the instance at the specified position in the array."""
        # Check in range
        if key >= len(self) or key < -len(self):
            raise IndexError("array index {} out of range".format(key))
        
        # Check the type
        if (not hasattr(instance, "data_type") or
                instance.data_type != self.data_type.base_type):
            raise TypeError("array is for type {} but got {}".format(
                self.data_type.base_type, repr(instance)))
        
        # Set the element's address
        if self.address is None:
            instance.address = None
        else:
            instance.address = self.address + (instance.size * key)
        
        # If there was previously an instance here, remove this array as its
        # container.
        if self._instances[key] is not None:
            self._instances[key]._parents.remove(self)
        
        self._instances[key] = instance
        
        # We are now the instance's parent, add it to the list
        instance._parents.append(self)
        
        # The array has now been changed, inform any parents
        self._value_changed()
    
    def _child_value_changed(self, child):
        if not self._ignore_child_value_changed:
            self._value_changed()
    
    def _child_address_changed(self, child):
        # Simply verify that the new address is appropriate, if not fail and
        # revert the address.
        if self.address is None:
            address = None
        else:
            key = self._instances.index(child)
            address = self.address + (key * child.size)
        
        if child.address != address:
            # If the address is bad, fix it and throw an error.
            child.address = address
            raise ValueError("The address of {} is defined by its "
                             "containing array, {}, as {}".format(
                                 repr(child), repr(self), self.address))
    
    @property
    def size(self):
        if self.data_type.length == 0:
            # We need an instance to know the size of a type but an array of
            # length zero is always of size 0.
            return 0
        else:
            return self.data_type.length * self._instances[0].size
    
    @property
    def literal(self):
        length = self.data_type.length
        return "{{{}}}".format(", ".join(i.literal for i in self._instances))
    
    def pack(self, endianness=Endianness.little):
        return b"".join(i.pack(endianness) for i in self._instances)
    
    def unpack(self, data, endianness=Endianness.little):
        self._ignore_child_value_changed = True
        for instance in self._instances:
            this_data, data = data[:instance.size], data[instance.size:]
            instance.unpack(this_data, endianness)
        self._ignore_child_value_changed = False
        
        self._value_changed()
    
    def __str__(self):
        return "[{}]".format(", ".join(map(str, self._instances)))
    
    def iter_references(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        for instance in self._instances:
            for r in instance.iter_references(_generated):
                yield r

