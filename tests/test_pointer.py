import pytest

from mock import Mock

from cdata.endianness import Endianness

from cdata.pointer import Pointer, PointerInstance

from cdata.primitive import char, _Bool

from cdata.exceptions import PointerToUndefinedMemoryAddress

def test_pointer():
    char_p = Pointer(char)
    
    # Check all type information is correct
    assert char_p.name == "char*"
    assert char_p.native == True
    assert char_p.prototype == ""
    assert char_p.definition == ""
    assert char_p.declare() == "char*"
    assert char_p.declare("magic") == "char* magic"
    assert list(char_p.iter_types()) == [char, char_p]
    assert repr(char_p) == "<Pointer: char*>"
    
    # Check creating an instance produces the correct type
    c = char_p()
    assert c.data_type is char_p
    assert isinstance(c, PointerInstance)


def test_null():
    char_p = Pointer(char)

    # Check that the pointer defaults to being NULL
    c = char_p()
    assert c.ref == 0
    assert c.deref is None
    
    # Check the standard features work when NULL.
    assert c.address is None
    assert c.size == 4
    assert c.literal == "NULL"
    assert c.pack() == b"\x00\x00\x00\x00"
    assert str(c) == "NULL"
    assert repr(c) == "<char*: NULL>"
    assert list(c.iter_references()) == []
    
    # Check that assigning an address of 0 produces a null pointer too
    c = char_p(0)
    assert c.ref == 0
    assert c.deref is None
    assert c.pack() == b"\x00\x00\x00\x00"
    
    # Check that setting the pointer to an instance with address 0 sets the
    # pointer to Null too.
    my_char = char()
    my_char.address = 0
    c = char_p(my_char)
    assert c.ref == 0
    assert c.deref is None
    assert c.pack() == b"\x00\x00\x00\x00"
    
    # Check that changing a child's address to 0 results in a NULL pointer
    my_char = char()
    c = char_p(my_char)
    assert c.deref is my_char
    c.deref.address = 0
    assert c.ref == 0
    assert c.deref is None
    assert c.pack() == b"\x00\x00\x00\x00"
    
    # Check that unpacking a NULL pointer produces a null
    c.unpack(b"\x00\x00\x00\x00")
    assert c.ref == 0
    assert c.deref is None
    assert c.pack() == b"\x00\x00\x00\x00"


def test_not_null():
    char_p = Pointer(char)
    
    # Should get a default character instance if we pass in a non-0 address
    c = char_p(0xDEADBEEF)
    assert c.ref == 0xDEADBEEF
    assert c.deref is not None
    assert c.deref.data_type is char
    assert c.deref.value == char().value
    
    # The pointer should reference the pointed-to value
    assert list(c.iter_references()) == [c.deref]
    
    # Check the standard features work when not-NULL.
    c.deref.value = b"J"
    assert c.address is None
    assert c.size == 4
    assert c.literal == "&'J'"
    assert c.pack() == b"\xEF\xBE\xAD\xDE"
    assert str(c) == "b'J'"
    assert repr(c) == "<char*: b'J'>"
    
    # If a NULL pointer is given a new Non-NULL address (either manually or by
    # unpacking), a new default instance should be created.
    c = char_p()
    assert c.ref == 0
    assert c.deref is None
    c.ref = 0xDEADBEEF
    assert c.ref == 0xDEADBEEF
    assert c.deref is not None
    assert c.deref.value == b"\0"
    assert c.deref.address == 0xDEADBEEF
    
    c = char_p()
    assert c.ref == 0
    assert c.deref is None
    c.unpack(b"\xFF\xFF\xFF\xFF")
    assert c.ref == 0xFFFFFFFF
    assert c.deref is not None
    assert c.deref.value == b"\0"
    assert c.deref.address == 0xFFFFFFFF
    
    # If we don't change the pointer ref, the underlying character instance
    # referenced should not be touched
    referenced_char_inst = c.deref
    referenced_char_inst.value = b"J"
    referenced_char_inst.address = 0xDEADBEEF
    c.unpack(b"\xEF\xBE\xAD\xDE")
    assert c.ref == 0xDEADBEEF
    assert c.deref is referenced_char_inst
    
    # If we do change the pointer address, the underlying character instance
    # should be replaced
    c.unpack(b"\x78\x56\x34\x12")
    assert c.ref == 0x12345678
    assert c.deref is not referenced_char_inst
    assert c.deref.address == 0x12345678
    assert c.deref.value == b"\0"

@pytest.mark.parametrize("n_bits", [8, 16, 32, 64])
def test_lengths(n_bits):
    # Check that addresses of different lengths and endiannesses can be
    # packed/unpacked.
    
    char_p = Pointer(char, n_bits)
    address = sum((n + 1) << n for n in range(0, n_bits, 8))
    
    # Addresses should fail out of the allowed range...
    for bad_address in [-1, 1 << n_bits, address | (1 << n_bits)]:
        # ...when set by constructor...
        with pytest.raises(ValueError):
            char_p(bad_address)
        
        # ...when set by ref...
        c = char_p(char())
        with pytest.raises(ValueError):
            c.ref = bad_address
        
        # ...when set by the child's address field.
        with pytest.raises(ValueError):
            c.deref.address = bad_address
    
    c = char_p(address)
    referenced_char_inst = c.deref
    
    # Should have the right number of bits in the packed form
    for endianness in Endianness:
        # Work out what the packed form of the address will be
        packed_address = bytes((address >> n) & 0xFF
                               for n in range(0, n_bits, 8))
        if endianness == Endianness.big:
            packed_address = bytes(reversed(packed_address))
        
        # Address should be the right length once packed
        assert len(c.pack(endianness)) == n_bits // 8
        assert c.pack(endianness) == packed_address
        
        # Pack/unpack shouldn't change the address and thus shouldn't change the
        # underlying value instance.
        c.unpack(c.pack(endianness), endianness)
        assert c.deref.address == address
        assert c.deref is referenced_char_inst


def test_unsupported_length():
    # Attempting to generate a pointer of an unsupported length should fail
    with pytest.raises(ValueError):
        Pointer(char, 48)


def test_pack_unknown_address():
    # Attempting to pack a pointer to an instance without an address should
    # fail.
    char_p = Pointer(char)
    c = char_p(char())
    assert c.ref is None
    with pytest.raises(PointerToUndefinedMemoryAddress):
        c.pack()


def test_wrong_type():
    # Attempting to create a pointer to an instance with the wrong type should
    # fail
    char_p = Pointer(char)
    
    with pytest.raises(TypeError):
        c = char_p(_Bool())
    
    c = char_p()
    with pytest.raises(TypeError):
        c.deref = _Bool()


def test_double_pointer():
    # Create a double pointer
    char_pp = Pointer(Pointer(char))
    
    # Type list should be extended to include the intermediate pointer type
    assert list(char_pp.iter_types()) == [char, Pointer(char), char_pp]
    
    # Check naming
    assert char_pp.name == "char**"
    assert char_pp.declare() == "char**"
    assert char_pp.declare("magic") == "char** magic"
    
    c = char_pp(Pointer(char)(char(b"J")))
    
    # Should dereference correctly
    assert c.deref.deref.value == b"J"
    
    # Should have an appropriate literal
    assert c.literal == "&&'J'"
    
    # Should recursively list references
    assert list(c.iter_references()) == [c.deref, c.deref.deref]


def test_parent():
    # Make sure parent container/reference types get called when appropriate.
    char_p = Pointer(char)
    c = char_p(char())
    
    container = Mock()
    c._parents.append(container)
    
    # Should not get informed on pointed-to value changes
    c.deref.value = b"J"
    assert not container._child_value_changed.mock_calls
    assert not container._child_address_changed.mock_calls
    
    # Should get informed when the pointer's address is changed
    c.ref = 0xDEADBEEF
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    
    # Should get informed when the child's address changes
    c.deref.address = 0x12345678
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    
    # Should get informed when child gets nulled-out
    c.ref = 0
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    
    # Should get informed when child gets swapped
    c.deref = char()
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    
    # Should get informed when child gets indirectly nulled-out
    c.deref.address = 0
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    
    # Nulling out a pointer should stop its instance causing change
    # notifications.
    my_char = char()
    c.deref = my_char
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    my_char.address = 0x1234
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    my_char.address = 0
    container._child_value_changed.assert_called_once_with(c)
    container._child_value_changed.reset_mock()
    assert not container._child_address_changed.mock_calls
    my_char.address = 0x1234
    assert not container._child_value_changed.mock_calls
    assert not container._child_address_changed.mock_calls
    
    # Should get informed of address changes as usual
    c.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(c)
