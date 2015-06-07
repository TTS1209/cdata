import pytest

from mock import Mock

from cdata.struct import Struct, StructInstance

from cdata.primitive import char, unsigned_char

from cdata.endianness import Endianness

def test_struct():
    struct_test = Struct("test",
                         ("a", char),
                         ("b", unsigned_char))
    
    # Check the type looks sensible (more fully tested by the ComplexType tests
    assert struct_test.name == "struct test"
    assert struct_test.native == False
    assert struct_test.prototype == "struct test;"
    assert struct_test.definition == ("struct test {\n"
                                      "    char a;\n"
                                      "    unsigned char b;\n"
                                      "};")
    assert struct_test.declare() == ("struct test")
    assert struct_test.declare("magic") == ("struct test magic")
    assert list(struct_test.iter_types()) == [char, unsigned_char, struct_test]
    assert repr(struct_test) == "<Struct: struct test>"
    
    # Check the instances look sensible (again, the ComplexTypeInstance base
    # class is more fully tested elsewhere)
    t = struct_test(char(b"J"), unsigned_char(255))
    assert isinstance(t, StructInstance)
    assert t.a.value == b"J"
    assert t.b.value == 255
    assert t.data_type == struct_test
    assert t.size == 2
    assert t.literal == ("(struct test){\n"
                         "    'J',\n"
                         "    255\n"
                         "}")
    assert str(t) == "{a: b'J', b: 255}"
    assert repr(t) == "<struct test: {a: b'J', b: 255}>"
    
    # Should be able to change the address which should change all members
    # addresses too
    assert t.address is None
    t.address = 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1001
    t.address = None
    assert t.a.address is None
    assert t.b.address is None
    
    # Should be able to change the addresses of children to the correct value
    # with no complaints
    t.address = None
    t.a.address = None
    t.b.address = None
    assert t.address is None
    assert t.a.address is None
    assert t.b.address is None
    
    t.address = 0x1000
    t.a.address = 0x1000
    t.b.address = 0x1001
    assert t.address == 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1001
    
    # If a new instance is inserted, its address should be assigned
    uc = unsigned_char(t.b.value)
    uc.address = 0xDEADBEEF
    t.b = uc
    assert uc.address == 0x1001
    
    # Should get an error if the address is changed erroneously
    with pytest.raises(ValueError):
        t.a.address = 0xFFFF
    with pytest.raises(ValueError):
        t.b.address = 0xFFFF
    assert t.address == 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1001
    
    t.address = None
    with pytest.raises(ValueError):
        t.a.address = 0xFFFF
    with pytest.raises(ValueError):
        t.b.address = 0xFFFF
    assert t.address is None
    assert t.a.address is None
    assert t.b.address is None
    
    # Packing should work and, because both struct elements are bytes, the
    # ordering should not be changed by endianness.
    for endianness in Endianness:
        assert t.pack(endianness) == b"J\xFF"
    
    # Unpacking should do the same
    for endianness in Endianness:
        t = struct_test()
        t.unpack(b"H\xAA", endianness)
        assert t.a.value == b"H"
        assert t.b.value == 0xAA


def test_container():
    struct_test = Struct("test",
                         ("a", char),
                         ("b", unsigned_char))
    s = struct_test()
    
    container = Mock()
    s._parents.append(container)
    
    # Changing the address should cause a callback
    s.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(s)
    container._child_address_changed.reset_mock()
    
    # Changing a struct member's address shouldn't
    s.a.address = 0xDEADBEEF
    assert not container._child_address_changed.called
    
    # Changing a struct member's value should cause a callback (more
    # exhaustively tested by ComplexType base class)
    s.a.value = b"J"
    container._child_value_changed.assert_called_once_with(s)
    container._child_value_changed.reset_mock()
