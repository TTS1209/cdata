"""The base classes for CData types."""


from cdata.exceptions import PointerToUndefinedMemoryAddress

from cdata.endianness import Endianness

from cdata.utils import empty_iterable


class DataType(object):
    """The base-class for all CData types.
    
    Attributes
    ----------
    name : str or None
        The C identifier (name) of this type or None if this type is anonymous.
    native : bool
        Is this type native to C (or the standard-library)?
    doc : str
        An (optionally defined) string which describes the purpose of this type.
        This will be prepended as a comment to the definition of the type, if it
        has one.
    prototype : str
        The C type prototype for this data type (often blank).
    definition : str
        The C type definition for this data type (often blank).
    """
    
    # Placed here so that these names appear in the dir() of this class to allow
    # discovery of the names used by the class before it is instantiateed. This
    # is useful since some datatypes may wish to add user-defined attributes to
    # an Instance object and therefore it is important that any names which are
    # reserved are known.
    name = None
    native = None
    
    def __init__(self, name=None, native=False, doc=""):
        """Define a new data type.
        
        Parameters
        ----------
        name : str or None
            The C identifier (name) of this type or the full type if it is
            anonymous.
        native : bool
            Is this type native to C (or the standard-library)?
        doc : str
            An (optionally defined) string which describes the purpose of this
            type. This will be prepended as a comment to the definition of the
            type, if it has one.
        """
        self.name = name
        self.native = native
        self.doc = doc
        
        # Set the datatype's docstring accordingly.
        if doc:
            self.__doc__ = doc
    
    def __call__(self):
        """Instantiate a new instance of this data type with the values passed
        as arguments.
        
        Returns
        -------
        :py:class:`.Instance`
            An instance of this data type.
        """
        raise NotImplementedError()
    
    @property
    def prototype(self):
        """The C prototype definition of this data type.
        
        Many types (including all native types) do not have a prototype and so
        this value is empty.
        """
        # The common case, there is no prototype
        return ""
    
    @property
    def definition(self):
        """The C type definition of this data type.
        
        Many types (including all native types) do not have a type defintion and so
        this value is empty.
        """
        # The common case, there is no definition
        return ""
    
    def declare(self, identifier=""):
        """Get a C declaration for variable of this type with the specified
        identifier.
        
        Parameters
        ----------
        identifier : str
            (Optional) The identifier for the variable to declare.
        
        Returns
        -------
        str
            The declaration without without any terminating semicolon.
        """
        # The common case (for simpler types)
        return "{} {}".format(self.name, identifier).strip()
    
    def iter_types(self, _generated=None):
        """Returns an generator which iterates over the set of data types used
        by this data type (including this data type itself).
        
        The iterator iterates in an order such that data types referring to or
        containing other data types are listed after the types they refer
        to/contain.
        
        The result lists each type exactly once and uniqueifies the types by
        their name.
        
        Parameters
        ----------
        _generated : set([:py:class:`DataType`, ...]) or None
            For internal use only. If :py:meth:`.iter_types` is called on a
            DataType whose *name* is listed in the _generated set, this
            generator should generate no values.
        """
        # A sensible iterator for types which don't contain other types.
        if _generated is None:
            _generated = set()
        if self.name not in _generated:
            _generated.add(self.name)
            yield self

    def __eq__(self, other):
        """Two types are equal if they have the same name. It is the
        responsibility of the user to ensure that no names are reused
        eroniously."""
        return hasattr(other, "name") and self.name == other.name

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.name)


class Instance(object):
    """The base-class for all CData type instances.
    
    Instance implementers should call :py:meth:`._value_changed` whenever the
    instance's value changes and :py:meth:`._address_changed` whenever the
    address changes.
    
    Implementations of container (e.g. struct) and reference (e.g. pointer)
    types should implement :py:meth:`._child_value_changed` and
    :py:meth:`._child_address_changed`. Note that the supplied "address" is a
    property which automatically calls the :py:meth:`._child_address_changed`
    method when the address is set.
    
    Container and reference instances should add themselves to their
    member's/referee instance's _container or _referrer respectively.  They
    should remove themselves when they no longer contain/refer to the specified
    instance.
    
    Attributes
    ----------
    data_type : :py:class:`DataType`
        The data type of this instance.
    address : int or None
        The address of this instance in memory or None if undefined.
    size : int
        The size (in bytes) of the C representation of this instance.
    literal : str
        A C-literal which has the same value as this instance.
    _container : :py:class:`Instance` or None
        For internal use. The container instance which directly contains this
        instance or None if this instance is not in a container.
        
        Used by the :py:meth:`._address_changed` and
        :py:meth:`._value_changed` methods to call all parents'
        :py:meth:`._child_value_changed` and :py:meth:`._child_address_changed`
        methods and also used to implement iter_instances.
    _referrer : :py:class:`Instance` or None
        Similar to _container except indicates which, if any, instance directly
        refers to this instance (e.g. a pointer). This has the side-effect that
        only one pointer may exist to a given value at any given time.
        
        This is not considered by the iter_instances method.
    """
    
    # Placed here so that these names appear in the dir() of this class to allow
    # discovery of the names used by the class before it is instantiateed. This
    # is useful since some instances may wish to add user-defined attributes to
    # an Instance object and therefore it is important that any names which are
    # reserved are known.
    data_type = None
    _address = None
    _container = None
    _referrer = None
    
    def __init__(self, data_type):
        """Create a new instance of the specified type."""
        self.data_type = data_type
        self.address = None
        self._container = None
        self._referrer = None
    
    @property
    def address(self):
        """Get the address of this instance in memory (or None if unknown)."""
        return self._address
    
    @address.setter
    def address(self, address):
        """Set the address of this instance in memory (or None if unknown)."""
        self._address = address
        self._address_changed()
    
    @property
    def size(self):
        """Return the size of C-encoded form of this instance."""
        raise NotImplementedError()
    
    @property
    def literal(self):
        """A C-literal which has the same value as this instance."""
        raise NotImplementedError()
    
    def pack(self, endianness=Endianness.little):
        """Pack the C-encoded form of just this instance's value into a
        C-compatible form.
        
        Parameters
        ----------
        endianness : :py:class:`.Endianness`
            The endianness to use to represent packed values. (Default:
            little-endian). "Standard" sizes as defined by the :py:mod:`struct`
            module are used and no automatic structure padding is performed.
        
        Returns
        -------
        :py:class:`bytes`
            The packed representation of this instance.
        
        Raises
        ------
        PointerToUndefinedMemoryAddress
            If this instance contains a pointer to an instance not assigned an address
            (e.g. with :py:meth:`.alloc`).
        """
        raise NotImplementedError()
  
    def unpack(self, data, endianness=Endianness.little):
        """Unpack the C-encoded form of this instance's value into this instance.
        
        Note that any values referenced (but not contained) by this instance
        will not be updated.
        
        Parameters
        -------
        data : :py:class:`bytes`
            The packed data to unpack into this instance.
        endianness : :py:class:`.Endianness`
            The endianness to use to represent packed values. (Default:
            little-endian). "Standard" sizes as defined by the :py:mod:`struct`
            module are used and no automatic structure padding is performed.
        """
        raise NotImplementedError()
    
    def iter_instances(self, _generated=None):
        """Iterate over all instances in any way related to this instance.
        
        The purpose of this iterator is to give the caller a full list of all
        the instances which form a common data-structure in order to either
        allocate non-overlapping memory addresses or to facilitate the packing
        of all related pieces of the structure without having to manually
        specify each one.
        
        This iterator will only list "top-level" instances, i.e. instances which
        don't reside in a container (e.g. a Struct or Array). This means that if
        you have defined a struct, only the struct instance will be listed, the
        struct members are not (since when the struct is packed, all its members
        will be included). This iterator will also list any referenced
        instances, for example calling iter_instances on a Pointer will produce
        the pointer instance (or its container) along with the instance being
        pointed to (or its container).
        
        Parameters
        ----------
        _generated : set([:py:class:`Instance`, ...]) or None
            For internal use only. If :py:meth:`.iter_instances` is called on an
            instance which is listed in the _generated set, the generator
            should terminate immediately.
        """
        # This default implementation is sufficient for non-container and
        # non-reference types. Containers and reference types should extend this
        # method so that it also iterates over their members/referred instances.
        
        if _generated is None:
            _generated = set()
        
        # Don't generate this instance multiple times
        if self in _generated:
            return
        else:
            _generated.add(self)
        
        if not self._container:
            # If this instance is a top-level instance, produce itself
            yield self
        else:
            # This instance is in a container, list the container's instances
            # instead.
            for i in self._container.iter_instances(_generated):
                yield i
    
    def __str__(self):
        """Produce a human-readable version of the value of this instance."""
        raise NotImplementedError()
    
    def __repr__(self):
        return "<{}: {}>".format(self.data_type.name,
                                 str(self))
    
    def _value_changed(self):
        """To be called when an instances' value is changed."""
        if self._container is not None:
            self._container._child_value_changed(self)
        if self._referrer is not None:
            self._referrer._child_value_changed(self)
    
    def _address_changed(self):
        """To be called when an instances' address is changed."""
        if self._container is not None:
            self._container._child_address_changed(self)
        if self._referrer is not None:
            self._referrer._child_address_changed(self)
    
    def _child_value_changed(self, child):
        """Called for containers when a child's value changes."""
        raise NotImplementedError()
    
    def _child_address_changed(self, child):
        """Called for containers when a child's value changes."""
        raise NotImplementedError()
