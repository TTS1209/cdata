import pytest

from mock import Mock

from cdata.typedef import Typedef, TypedefInstance

from cdata.primitive import char

from cdata.pointer import Pointer

from mock_container import container

def test_typedef():
    char_t = Typedef("char_t", char)
    
    # Check all type information is correct
    assert char_t.name == "char_t"
    assert char_t.native == False
    assert char_t.prototype == ""
    assert char_t.definition == "typedef char char_t;"
    assert char_t.declare() == "char_t"
    assert char_t.declare("magic") == "char_t magic"
    assert list(char_t.iter_types()) == [char, char_t]
    assert repr(char_t) == "<Typedef: char_t>"
    
    # Check that the instance's constructor behaves like the underlying type
    c = char_t()
    assert c.value == b"\0"
    c = char_t(b"\xAB")
    assert c.value == b"\xAB"
    
    # Check the instance is actually of the typedef type
    c = char_t()
    assert isinstance(c, TypedefInstance)
    assert c.data_type is char_t
    assert c.literal == "(char_t)'\\x00'"
    assert list(c.iter_instances()) == [c]
    
    # Check that standard values pass through
    assert c.address is None
    c.value = b"\x42"  # "B"
    assert c.size == 1
    assert c.pack() == b"\x42"
    assert str(c) == "b'B'"
    assert repr(c) == "<char_t: b'B'>"
    
    # Check the instance remains of the correct type after unpacking
    c.unpack(b"\x12")
    assert c.value == b"\x12"


def test_iter_instances():
    # The typedef should also iterate over its wrapped instance.
    charp_t = Typedef("charp_t", Pointer(char))
    cpt = charp_t()
    assert list(cpt.iter_instances()) == [cpt]
    
    c = char()
    cpt.deref = c
    assert list(cpt.iter_instances()) == [cpt, c]

def test_parents(container):
    # Check that if the typedef is in a container or is referenced, the calls
    # are passed through correctly and that they give the typedef's instance,
    # not the underlying base type.
    char_t = Typedef("char_t", char)
    c = char_t()
    
    referrer = Mock()
    c._container = container
    c._referrer = referrer
    
    c.value = b"J"
    c.address = 0xDEADBEEF
    assert len(container._child_value_changed.call_args_list) == 1
    assert len(referrer._child_value_changed.call_args_list) == 1
    child = container._child_value_changed.call_args_list[0][0][0]
    child = referrer._child_value_changed.call_args_list[0][0][0]
    assert child is c
    
    assert len(container._child_address_changed.call_args_list) == 1
    assert len(referrer._child_address_changed.call_args_list) == 1
    child = container._child_address_changed.call_args_list[0][0][0]
    child = referrer._child_address_changed.call_args_list[0][0][0]
    assert child is c
    
    # Should iterate over the container, not the instance
    assert list(c.iter_instances()) == [container]


def test_typedef_documented():
    # Check that documentation gets added to the definition only.
    char_t = Typedef("char_t", char, doc="An example typedef.")
    
    assert char_t.name == "char_t"
    assert char_t.native == False
    assert char_t.prototype == ""
    assert char_t.definition == ("/* An example typedef. */\n"
                                 "typedef char char_t;")
    assert char_t.declare() == "char_t"
    assert char_t.declare("magic") == "char_t magic"
    assert list(char_t.iter_types()) == [char, char_t]
    assert repr(char_t) == "<Typedef: char_t>"


def test_multiple_typedef_instances():
    """This test ensures that multiple instances of a typedef can exist at once.
    This essentially verifies that the magic going on in the TypedefInstance
    class isn't causing all TypedefInstances to be the same.
    """
    char_t = Typedef("char_t", char)
    
    c0 = char_t(b"0")
    c1 = char_t(b"1")
    
    assert c0.value == b"0"
    assert c1.value == b"1"
