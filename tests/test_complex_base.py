import pytest

from mock import Mock

from six import itervalues

from cdata.primitive import char, unsigned_char

from cdata.pointer import Pointer

from cdata.complex_base import ComplexType, ComplexTypeInstance

from cdata.endianness import Endianness

class Foo(ComplexType):
    """Define an example complex type for the purposes of these tests."""
    
    def __init__(self, *args, native=False):
        super(Foo, self).__init__("foo", *args, native=native)
    
    def __call__(self, *args, **kwargs):
        return FooInstance(self, *args, **kwargs)


class FooInstance(ComplexTypeInstance):
    """An instance of the above example type."""
    
    @property
    def size(self):
        return 123
    
    def pack(self, endianness=Endianness.little):
        return b"foo"
    
    def unpack(self, data, endianness=Endianness.little):
        pass
    
    def _child_address_changed(self, child):
        # Just do nothing
        pass

def test_empty():
    # Test nothing falls over when creating empty types
    foo = Foo()
    assert foo.name == "foo {\n\n}"
    assert foo.native == False
    assert foo.prototype == ""
    assert foo.definition == ""
    assert foo.declare() == "foo {\n\n}"
    assert foo.declare("magic") == "foo {\n\n} magic"
    assert list(foo.iter_types()) == [foo]
    assert repr(foo) == "<Foo: foo {\n\n}>"
    
    f = foo()
    assert f.data_type == foo
    assert f.address is None
    assert f.size == 123  # From FooInstance
    assert f.pack() == b"foo"  # From FooInstance
    assert f.literal == "(foo {\n\n}){\n\n}"
    
    foo = Foo("empty")
    assert foo.name == "foo empty"
    assert foo.native == False
    assert foo.prototype == "foo empty;"
    assert foo.definition == "foo empty {\n\n};"
    assert foo.declare() == "foo empty"
    assert foo.declare("magic") == "foo empty magic"
    assert list(foo.iter_types()) == [foo]
    assert repr(foo) == "<Foo: foo empty>"
    
    f = foo()
    assert f.data_type == foo
    assert f.address is None
    assert f.size == 123  # From FooInstance
    assert f.pack() == b"foo"  # From FooInstance
    assert f.literal == "(foo empty){\n\n}"

def test_named():
    # Test that named complex types work and look right.
    
    my_foo = Foo("my_foo",
                 ("a", char),
                 ("b", unsigned_char))
    
    # Check the type's behaviour
    assert my_foo.name == "foo my_foo"
    assert my_foo.native == False
    assert my_foo.prototype == "foo my_foo;"
    assert my_foo.definition == ("foo my_foo {\n"
                                 "    char a;\n"
                                 "    unsigned char b;\n"
                                 "};")
    assert my_foo.declare() == "foo my_foo"
    assert my_foo.declare("magic") == "foo my_foo magic"
    assert list(my_foo.iter_types()) == [char, unsigned_char, my_foo]
    assert repr(my_foo) == "<Foo: foo my_foo>"


def test_anonymous():
    # Test that anonymous complex types work and look right.
    
    anon = Foo(("a", char),
               ("b", unsigned_char))
    
    # Check the type's behaviour
    assert anon.name == ("foo {\n"
                         "    char a;\n"
                         "    unsigned char b;\n"
                         "}")
    assert anon.native == False
    assert anon.prototype == ""
    assert anon.definition == ""
    assert anon.declare() == ("foo {\n"
                              "    char a;\n"
                              "    unsigned char b;\n"
                              "}")
    assert anon.declare("magic") == ("foo {\n"
                                     "    char a;\n"
                                     "    unsigned char b;\n"
                                     "} magic")
    assert list(anon.iter_types()) == [char, unsigned_char, anon]
    assert repr(anon) == ("<Foo: foo {\n"
                          "    char a;\n"
                          "    unsigned char b;\n"
                          "}>")

@pytest.mark.parametrize("name", ["_anything_with_a_leading_underscore",
                                  "anything_with_double__underscores",
                                  # Names used by the base type
                                  "data_type",
                                  "literal",
                                  "iter_references",
                                 ])
def test_reserved_names(name):
    # Test that some names are not allowed
    with pytest.raises(ValueError):
        Foo((name, char))


def test_instance():
    # Test that the basic functionality of instances works
    my_foo = Foo("my_foo",
                 ("a", char),
                 ("b", unsigned_char))
    
    # Make sure we can access the individual values (and they are the defaults
    # for each type)
    f = my_foo()
    assert f.a.value == b"\0"
    assert f.b.value == 0
    
    # Check we can pre-initialise the struct members
    f = my_foo(char(b"J"))
    assert f.a.value == b"J"
    assert f.b.value == 0
    
    f = my_foo(char(b"D"), unsigned_char(123))
    assert f.a.value == b"D"
    assert f.b.value == 123
    
    f = my_foo(b=unsigned_char(123))
    assert f.a.value == b"\0"
    assert f.b.value == 123
    
    f = my_foo(a=char(b"H"))
    assert f.a.value == b"H"
    assert f.b.value == 0
    
    f = my_foo(a=char(b"!"), b=unsigned_char(123))
    assert f.a.value == b"!"
    assert f.b.value == 123
    
    # Check we can't over-fill the struct
    with pytest.raises(ValueError):
        my_foo(char(), unsigned_char(), char())
    
    # Check we can't define anything more than once
    with pytest.raises(ValueError):
        my_foo(char(), a=char())
    
    # Check we can't provide the wrong types
    with pytest.raises(TypeError):
        my_foo(unsigned_char())
    with pytest.raises(TypeError):
        my_foo(b=char())
    
    # Check that all the usual facilities of the instance work as expected.
    f = my_foo()
    assert f.data_type == my_foo
    assert f.address == None
    f.address = 0xDEADBEEF
    assert f.address == 0xDEADBEEF
    assert f.size == 123  # From FooInstance
    assert f.literal == ("(foo my_foo){\n"
                         "    '\\x00',\n"
                         "    0\n"
                         "}")
    assert list(f.iter_references()) == []
    assert str(f) == "{a: b'\\x00', b: 0}"
    assert repr(f) == "<foo my_foo: {a: b'\\x00', b: 0}>"
    
    # Simply checks these *can* be overridden
    assert f.pack() == b"foo"  # From FooInstance
    f.unpack(b"foo")  # From FooInstance


def test_iter_references_with_pointers():
    # If some members are pointers, their destinations should be listed amongst
    # the references.
    c = char()
    uc = unsigned_char()
    
    pointy_foo = Foo("pointy_foo",
                     ("a", char),
                     ("b", unsigned_char),
                     ("c", Pointer(char)),
                     ("d", Pointer(unsigned_char)))
    
    assert list(pointy_foo.iter_types()) == [char, unsigned_char,
                                             Pointer(char),
                                             Pointer(unsigned_char),
                                             pointy_foo]
    
    f = pointy_foo(c=Pointer(char)(c),
                   d=Pointer(unsigned_char)(uc))
    assert list(f.iter_references()) == [c, uc]



def test_nested():
    # These complex types should nest correctly
    
    # A type with an anonymous complex type inside it
    anon_foo = Foo(("ba", char),
                   ("bb", unsigned_char))
    my_foo = Foo("my_foo",
                 ("a", char),
                 ("b", anon_foo))
    
    # The type should be correctly represented
    assert my_foo.prototype == "foo my_foo;"
    assert my_foo.definition == ("foo my_foo {\n"
                                 "    char a;\n"
                                 "    foo {\n"
                                 "        char ba;\n"
                                 "        unsigned char bb;\n"
                                 "    } b;\n"
                                 "};")
    assert my_foo.declare() == "foo my_foo"
    assert my_foo.declare("magic") == "foo my_foo magic"
    assert list(my_foo.iter_types()) == [char, unsigned_char, anon_foo, my_foo]
    assert repr(my_foo) == "<Foo: foo my_foo>"
    
    # Instances should default correctly
    f = my_foo()
    assert f.a.data_type == char
    assert f.a.value == b"\0"
    
    assert f.b.ba.data_type == char
    assert f.b.ba.value == b"\0"
    
    assert f.b.bb.data_type == unsigned_char
    assert f.b.bb.value == 0
    
    # Should be able to set initial instance for nested types
    f = my_foo(char(b"J"), anon_foo(char(b"H"), unsigned_char(90)))
    assert f.a.value == b"J"
    assert f.b.ba.value == b"H"
    assert f.b.bb.value == 90
    
    # And by name
    f = my_foo(a=char(b"J"), b=anon_foo(char(b"H"), unsigned_char(90)))
    assert f.a.value == b"J"
    assert f.b.ba.value == b"H"
    assert f.b.bb.value == 90
    
    # And recursively by name
    f = my_foo(a=char(b"J"), b__ba=char(b"H"), b__bb=unsigned_char(90))
    assert f.a.value == b"J"
    assert f.b.ba.value == b"H"
    assert f.b.bb.value == 90
    
    # Shouldn't be able to give recursive names for non-nested types
    with pytest.raises(ValueError):
        my_foo(a__no_exist=char())
    
    # Shouldn't be able to specify recursive names which don't exist in the
    # nested type.
    with pytest.raises(ValueError):
        my_foo(b__no_exist=char())
    
    # Shouldn't be able to specify a value both explicitly and recursively
    with pytest.raises(ValueError):
        my_foo(b=anon_foo(), b__ba=char())
    
    # And again but this time with the values given positionally
    with pytest.raises(ValueError):
        my_foo(char(), anon_foo(), b__ba=char())

def test_container():
    # Test that the object forwards value change events from all members, but
    # not members' address changes.
    my_foo = Foo("my_foo",
                 ("a", char),
                 ("b", unsigned_char))
    
    f = my_foo()
    container = Mock()
    f._parents.append(container)
    
    # Changing the children should cause events
    f.a.value = b"a"
    container._child_value_changed.assert_called_once_with(f)
    container._child_value_changed.reset_mock()
    f.b.value = 123
    container._child_value_changed.assert_called_once_with(f)
    container._child_value_changed.reset_mock()
    
    # Changing an instance should cause events too
    old_a = f.a
    f.a = char(b"J")
    container._child_value_changed.assert_called_once_with(f)
    container._child_value_changed.reset_mock()
    
    # ...and should have stopped us responding to the old instance
    old_a.value = b"X"
    assert not container._child_value_changed.called
    
    # Changing child addresses should be ignored
    f.a.address = 0xDEADBEEF
    assert not container._child_address_changed.called
    
    # Changing the main address should cause a callback
    f.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(f)
