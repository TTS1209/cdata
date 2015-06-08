import pytest

from mock import Mock

from cdata.array import Array, ArrayInstance

from cdata.primitive import unsigned_short, char

def test_array():
    # Check the type behaves as expected
    ushort3 = Array(unsigned_short, 3)
    
    assert ushort3.name == "unsigned short[3]"
    assert ushort3.native == True
    assert ushort3.prototype == ""
    assert ushort3.definition == ""
    assert ushort3.declare() == "unsigned short[3]"
    assert ushort3.declare("magic") == "unsigned short magic[3]"
    assert list(ushort3.iter_types()) == [unsigned_short, ushort3]
    
    # Check the instance behaves as expected.
    # The default constructor should result in default values
    a = ushort3()
    assert isinstance(a, ArrayInstance)
    assert a.data_type is ushort3
    assert a.address is None
    assert a.size == 6
    assert a.literal == "{0, 0, 0}"
    assert a.pack() == b"\0\0\0\0\0\0"
    a.unpack(b"\x11\x11\x22\x22\x33\x33")
    assert a[0].value == 0x1111
    assert a[1].value == 0x2222
    assert a[2].value == 0x3333
    assert list(a.iter_references()) == []
    assert str(a) == "[4369, 8738, 13107]"
    assert repr(a) == "<unsigned short[3]: [4369, 8738, 13107]>"
    
    # Should be able to access elements by negative indices
    assert a[-3].value == 0x1111
    assert a[-2].value == 0x2222
    assert a[-1].value == 0x3333
    
    # Setting the address should change the array members' addresses
    a.address = 0x1000
    assert a[0].address == 0x1000
    assert a[1].address == 0x1002
    assert a[2].address == 0x1004
    
    # Test array-like behaviour
    assert len(a) == 3
    assert list(a) == [a[0], a[1], a[2]]
    with pytest.raises(IndexError):
        a[3]
    with pytest.raises(IndexError):
        a[-4]
    with pytest.raises(IndexError):
        a[3] = 0x123
    with pytest.raises(IndexError):
        a[-4] = 0x123
    
    # Test assignment works and sets the address
    a[0] = unsigned_short(0x3333)
    a[2] = unsigned_short(0x1111)
    
    assert a[0].value == 0x3333
    assert a[0].address == 0x1000
    
    assert a[1].value == 0x2222
    assert a[1].address == 0x1002
    
    assert a[2].value == 0x1111
    assert a[2].address == 0x1004
    
    # Address should be clear-able
    a.address = None
    assert a[0].address is None
    assert a[1].address is None
    assert a[2].address is None
    
    # Check the constructor works correctly. Should be able to partially and
    # fully initialise
    a0 = unsigned_short(0x1234)
    a = ushort3([a0])
    assert a[0] is a0
    assert a[0].value == 0x1234
    assert a[1].value == 0
    assert a[2].value == 0
    
    a0 = unsigned_short(0x1234)
    a0.address = 0x1234
    a1 = unsigned_short(0x5678)
    a1.address = 0x5678
    a2 = unsigned_short(0x90AB)
    a2.address = 0x90AB
    a = ushort3([a0, a1, a2])
    assert a[0] is a0
    assert a[0].value == 0x1234
    assert a[0].address is None
    assert a[1] is a1
    assert a[1].value == 0x5678
    assert a[1].address is None
    assert a[2] is a2
    assert a[2].value == 0x90AB
    assert a[2].address is None

def test_type_check():
    # Shouldn't be able to initialise with or set the wrong types
    ushort3 = Array(unsigned_short, 3)
    
    with pytest.raises(TypeError):
        ushort3([123])
    with pytest.raises(TypeError):
        ushort3([char(b"J")])
    
    a = ushort3()
    with pytest.raises(TypeError):
        a[0] = 123
    with pytest.raises(TypeError):
        a[0] = char("J")

def test_address_check():
    # Shouldn't be able to set the wrong address for array members
    ushort3 = Array(unsigned_short, 3)
    
    a = ushort3()
    a.address = 0x1000
    
    a[0].address = 0x1000
    with pytest.raises(ValueError):
        a[0].address = 0x2000
    assert a[0].address == 0x1000
    
    a[1].address = 0x1002
    with pytest.raises(ValueError):
        a[1].address = 0x2002
    assert a[1].address == 0x1002
    
    a[2].address = 0x1004
    with pytest.raises(ValueError):
        a[2].address = 0x2004
    assert a[2].address == 0x1004
    

def test_zero_length():
    # Check nothing goes badly wrong with arrays of length 0
    ushort0 = Array(unsigned_short, 0)
    
    assert ushort0.name == "unsigned short[0]"
    assert list(ushort0.iter_types()) == [unsigned_short, ushort0]
    
    a = ushort0()
    assert a.address is None
    assert a.size == 0
    assert a.literal == "{}"
    assert a.pack() == b""
    a.unpack(b"")
    assert list(a.iter_references()) == []
    assert str(a) == "[]"
    assert repr(a) == "<unsigned short[0]: []>"
    
    a.address = 0xDEADBEEF
    assert a.address == 0xDEADBEEF
    
    assert len(a) == 0
    assert list(a) == []

def test_container():
    ushort3 = Array(unsigned_short, 3)
    
    # Make sure the array sets up the _parents field of all members on
    # initialisation.
    a0 = unsigned_short(0x1234)
    a = ushort3([a0])
    assert a in a0._parents
    assert a in a[0]._parents
    assert a in a[1]._parents
    assert a in a[2]._parents
    
    # Make sure on instance replacement the parents field is updated
    a[0] = unsigned_short(0xBEEF)
    assert a not in a0._parents
    assert a in a[0]._parents
    
    # Make sure the parent isn't removed if the instance isn't replaced (e.g.
    # due to type check failure)
    a[0] = a0
    with pytest.raises(TypeError):
        a[0] = char(b"F")
    assert a[0] is a0
    assert a in a[0]._parents
    
    # Make sure that child changes are reported by the parent
    container = Mock()
    a._parents.append(container)
    
    a[0].value = 0x1111
    container._child_value_changed.assert_called_once_with(a)
    container._child_value_changed.reset_mock()
    
    # Assigning a new instance should also cause a value change
    a[0] = unsigned_short()
    container._child_value_changed.assert_called_once_with(a)
    container._child_value_changed.reset_mock()
    
    # So should unpacking (but only once)
    a.unpack(b"\0\0\0\0\0\0")
    container._child_value_changed.assert_called_once_with(a)
    container._child_value_changed.reset_mock()
    
    # Setting a child's address should not do anything since a child's address
    # cannot be changed.
    a[2].address = None
    assert not container._child_address_changed.called

    # Setting the address should result in a notification
    a.address = 0x1000
    container._child_address_changed.assert_called_once_with(a)
    container._child_address_changed.reset_mock()
