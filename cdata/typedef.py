"""Allow definition of C typedefs of existing types."""

from cdata.base import DataType, Instance

class Typedef(DataType):
    """Creates a typedef alias for the supplied type."""
    
    def __init__(self, name, base_type, native=False):
        self.base_type = base_type
        super(Typedef, self).__init__(name, native)
    
    def __call__(self, *args, **kwargs):
        return TypedefInstance(self, *args, **kwargs)
    
    @property
    def definition(self):
        return "typedef {};".format(self.base_type.declare(self.name))
    
    def iter_types(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        if self.name not in _generated:
            _generated.add(self.name)
            
            # First generate the type this typedef refers to
            for t in self.base_type.iter_types(_generated):
                yield t
            
            # Now generate the typedef itself
            yield self


class TypedefInstance(Instance):
    """An instance of a typedef'd type.
    
    This class essentially acts as a thin wrapper around the typedef'd type and
    all it really does is change the __repr__ function to make it more obvious
    that something is going on.
    """
    
    def __init__(self, typedef, *args, **kwargs):
        super(TypedefInstance, self).__init__(typedef)
    
    @property
    def literal(self):
        return "({}){}".format(self.data_type.name,
                               self._base_instance.literal)
    
    # A list of members of this method which this instance overrides (i.e. which
    # __getattribute__ and __setattr__ shouldn't intercept).
    OVERRIDDEN_MEMBERS = set([
        "data_type",
        "literal",
    ])
    
    def __getattribute__(self, attr):
        if attr in type(self).OVERRIDDEN_MEMBERS or attr.startswith("_"):
            return super(TypedefInstance, self).__getattribute__(attr)
        else:
            _base_instance = \
                super(TypedefInstance, self).__getattribute__("_base_instance")
            return getattr(_base_instance, attr)
    
    def __setattr__(self, attr, value):
        if attr in type(self).OVERRIDDEN_MEMBERS or attr.startswith("_"):
            super(TypedefInstance, self).__setattr__(attr, value)
        else:
            self._base_instance.__setattr__(attr, value)
    
    
    # The set of all special functions of the base type which will be wrapped by
    # this class. This set notably excludes __repr__ to ensure this class is
    # printed differently.
    WRAPPABLE_FUNCTIONS = set([
        "__str__", "__bytes__", "__format__", "__lt__", "__le__", "__eq__",
        "__ne__", "__gt__", "__ge__", "__hash__", "__bool__", "__delattr__",
        "__get__", "__set__", "__delete__", "__call__", "__len__",
        "__getitem__", "__setitem__", "__delitem__", "__iter__", "__reversed__",
        "__contains__"])
    
    def __new__(cls, typedef, *args, **kwargs):
        """Set up the TypedefInstance such that it wraps all special functions
        of the wrapped type."""
        # First create subclass off the TypedefInstance since we need to modify
        # it to include the wrapped special methods
        cls = type(cls.__name__, (cls, ), {})
        
        # Create the base type instance and embed a reference to it in the class
        cls._base_instance = typedef.base_type(*args, **kwargs)
        
        # Next add any magic methods from the function being wrapped. This is
        # required since Python can call these directly without going via
        # __getattribute__.
        for attr in dir(cls._base_instance):
            if attr in cls.WRAPPABLE_FUNCTIONS:
                setattr(cls, attr, getattr(cls._base_instance, attr))

        return super(TypedefInstance, cls).__new__(cls)
