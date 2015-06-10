import pytest

from cdata.array import Array

from cdata.pointer import Pointer

from cdata.primitive import char

from cdata.alloc import total_size, alloc

def test_total_size():
    # Sizes of stand-alone types should be the obvious values
    assert total_size(char()) == 1
    assert total_size(Pointer(char)()) == 4  # Note: a null pointer!
    
    # Test that when a non-null pointer is used, space is allocated for the
    # pointer's target is made.
    assert total_size(Pointer(char)(char())) == 5
    
    # Test that the total array size is counted (but elements in the array
    # aren't counted as individuals)
    assert total_size(Array(char, 8)()) == 8

def test_alloc():
    # Test that stand-alone types get allocated the supplied address
    c = char()
    assert alloc(c, 0x1000) == 0x1001
    assert c.address == 0x1000
    
    # Test that NULL pointers get assigned addresses
    p = Pointer(char)()
    assert alloc(p, 0x1000) == 0x1004
    assert p.address == 0x1000
    
    # Test that non-null pointers get assigned addresses, along with their
    # targets.
    p.deref = c
    assert alloc(p, 0x1000) == 0x1005
    assert p.address == 0x1000
    assert c.address == 0x1004
    
    # Test that container types get allocated for but their contents is not
    # allocated again separately.
    a = Array(char, 8)()
    assert alloc(a, 0x1000) == 0x1008
    assert a.address == 0x1000
    
