"""The base class which implements type functionality common to struct and union
types."""

from six import iteritems, itervalues

from collections import defaultdict, OrderedDict

from cdata.base import DataType, Instance

from cdata.utils import indent, comment


class ComplexType(DataType):
    """The base type for C structs and unions."""
    
    def __init__(self, complex_type, *args, native=False, doc=""):
        """Define a complex type.
        
        Parameters
        ----------
        complex_type : str
            The type of complex type (e.g. 'struct' or 'union').
        complex_type_name : str
            The name of the complex type (e.g. if complex_type is 'struct' and
            complex_type_name is 'foo', the new type is called 'struct foo'). If
            omitted, the type will be defined anonymously, i.e. suitable for
            nesting or typedefing.
        *members : (name, :py:class:`.DataType`, doc), ...
            The remaining arguments must be a set of member names and their
            types. These arguments may optionally additionally include a
            documentation string which describes the member. If present, this
            documentation is printed as a comment in the definition of the
            struct.
        """
        self._complex_type = complex_type
        
        # If the first argument is a string, it must be the struct name.
        if len(args) >= 1 and isinstance(args[0], str):
            self._complex_type_name = args[0]
            args = args[1:]
        else:
            self._complex_type_name = None
        
        # The remaining arguments list the struct's members.
        self._members = OrderedDict()
        self._member_docs = OrderedDict()
        for name_data_type_doc in args:
            if len(name_data_type_doc) == 2:
                name, data_type = name_data_type_doc
                member_doc = ""
            else:
                name, data_type, member_doc = name_data_type_doc
            
            self._members[name] = data_type
            self._member_docs[name] = member_doc
        
        # Make sure the complex type's member names do not clash with any
        # members of the ComplexTypeInstance class (since the members are
        # accessed via attribute of the class).
        clashes = set(self._members).intersection(
            set(dir(ComplexTypeInstance)))
        # Also ban anything starting with "_" (i.e. so we can't override
        # anything internal) and anything with "__" used in the middle since
        # this is used in place of "." when constructing nested complex types.
        clashes.update(name for name in self._members
                       if name.startswith("_") or "__" in name)
        if clashes:
            raise ValueError("{} {} reserved member name{}".format(
                ", ".join(clashes),
                "is a" if len(clashes) == 1 else "are",
                "" if len(clashes) == 1 else "s"))
        
        # Determine the full type name
        if self._complex_type_name is not None:
            # If the type is named, the type name is simple.
            name = "{} {}".format(self._complex_type,
                                  self._complex_type_name)
        else:
            # If the type is anonymous, its name is its full definition (less
            # the semicolon)
            name = self._definition.rstrip(";")
        super(ComplexType, self).__init__(name=name, native=native, doc=doc)
    
    @property
    def prototype(self):
        # Non-anonymous complex types *do* have prototypes
        if self._complex_type_name is not None:
            return "{} {};".format(self._complex_type,
                                   self._complex_type_name)
        else:
            return ""
    
    @property
    def definition(self):
        # Non-anonymous complex types *do* have definitions
        if self._complex_type_name is not None:
            if self.doc:
                return "{}\n{}".format(comment(self.doc), self._definition)
            else:
                return self._definition
        else:
            return ""
    
    
    @property
    def _definition(self):
        """The full definition of this type, even if it is anonymous."""
        member_declarations = []
        for name, data_type in iteritems(self._members):
            declaration = "{};".format(data_type.declare(name))
            
            member_doc = self._member_docs[name]
            if member_doc:
                declaration = "{}\n{}".format(comment(member_doc), declaration)
            
            member_declarations.append(declaration)
            
        members = "\n".join(member_declarations)
        
        return ("{} {}{{\n"
                "{}\n"
                "}};").format(self._complex_type,
                              "{} ".format(self._complex_type_name)
                                  if self._complex_type_name is not None
                                  else "",
                              indent(members))
    
    def iter_types(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        if self.name not in _generated:
            _generated.add(self.name)
            
            # Generate the types of all contained types first
            for data_type in itervalues(self._members):
                for t in data_type.iter_types(_generated):
                    yield t
            
            # Then generate this complex type
            yield self


class ComplexTypeInstance(Instance):
    """A generic instance of a complex type."""
    
    
    def __init__(self, data_type, *args, **kwargs):
        """Create a new instance of a complex type.
        
        Parameters
        ----------
        *args : [:py:class:`.Instance`, ...]
        *kwargs : {member_name: :py:class:`.Instance`, ...}
        """
        # Create a mapping from member names to their instances. This must be
        # done before anything else since all getter/setter operations require
        # that they can check attributes are not in this dictionary.
        self._member_instances = OrderedDict(
            (name, None) for name in data_type._members)
        
        super(ComplexTypeInstance, self).__init__(data_type)
        
        # Sanity check that we've not received more positional members than the
        # struct contains (the loop below would otherwise silently ignore this)
        if len(args) > len(self._member_instances):
            raise ValueError("{} only contains {} members, {} given".format(
                self.data_type.name, len(self._member_instances), len(args)))
        
        # Populate any positionally specified members
        for name, instance in zip(self._member_instances, args):
            setattr(self, name, instance)
        
        # Populate any named members, checking for multiple-definitions and
        # skipping (but recording) any definitions of members in nested complex
        # types.
        # {member_name: {sub_member_name: instance, ...}}
        nested_args = defaultdict(dict)
        for name, instance in iteritems(kwargs):
            if "__" in name:
                # Record the initial values set for nested members
                name, __, sub_name = name.partition("__")
                
                # Fail if the member has already been defined
                if self._member_instances[name] is not None:
                    raise ValueError("{} defined twice".format(name))
                
                # Save for later
                nested_args[name][sub_name] = instance
            else:
                # Set non-nested kwargs immediately
                
                # Fail if the name isn't a valid member
                if name not in self._member_instances:
                    raise ValueError("{} does not have a member {}".format(
                        self.data_type.name, name))
                
                # Fail if the member has already been defined
                if self._member_instances[name] is not None or name in nested_args:
                    raise ValueError("{} defined twice".format(name))
                
                # Actually set the member's value
                setattr(self, name, instance)
        
        # Populate any undefined members with new instances (note that the
        # iterator must be copied since we may mutate the dictionary)
        for name, instance in list(iteritems(self._member_instances)):
            if instance is None:
                data_type = self.data_type._members[name]
                
                # Fail if nested initialisation values are given but the type
                # isn't a ComplexType.
                kwargs = nested_args[name]
                if kwargs and not isinstance(data_type, ComplexType):
                    raise ValueError(
                        "member {} does not support sub-members".format(
                            name))
                
                setattr(self, name, data_type(**kwargs))
    
    def _get_member(self, name):
        """Underlying function to fetch member instances.
        
        This function will always be called with a valid member name.
        """
        return self._member_instances[name]
    
    def _set_member(self, name, instance):
        """Underlying function to set member instances.
        
        This function will always be called with a valid member name and
        instance type.
        """
        # If replacing an existing member, record that we are no-longer its
        # parent.
        if self._member_instances.get(name, None) is not None:
            self._member_instances[name]._parents.remove(self)
        
        self._member_instances[name] = instance
        instance._parents.append(self)
        
        self._child_value_changed(instance)
    
    def __getattr__(self, name):
        """Handles reads of member instances."""
        if name in self._member_instances:
            return self._get_member(name)
        else:
            raise AttributeError(name)
    
    def __setattr__(self, name, value):
        """Handles writes to member instances."""
        if not name.startswith("_") and name in self._member_instances:
            # Check that the value is of the correct type before accepting the
            # new value
            if (not hasattr(value, "data_type") or
                    value.data_type != self.data_type._members[name]):
                raise TypeError("member {} is of type {} but got {}".format(
                    name, repr(self.data_type), repr(value)))
            self._set_member(name, value)
        else:
            super(ComplexTypeInstance, self).__setattr__(name, value)
    
    @property
    def literal(self):
        member_literals = ",\n".join(
            t.literal for t in itervalues(self._member_instances))
        
        return ("({}){{\n"
                "{}\n"
                "}}").format(self.data_type.name, indent(member_literals))

    def iter_references(self, _generated=None):
        if _generated is None:
            _generated = set()
        
        # Iterate over any references in members (complex types don't inherently
        # reference anything so no need to list anything else).
        for instance in itervalues(self._member_instances):
            for ref in instance.iter_references(_generated):
                yield ref

    def __str__(self):
        return "{{{}}}".format(
            ", ".join("{}: {}".format(name, str(instance))
                      for name, instance
                      in iteritems(self._member_instances)))
