import pytest

from mock import Mock

from cdata.union import Union, UnionInstance

from cdata.primitive import unsigned_char, unsigned_short

from cdata.endianness import Endianness

def test_union():
    union_test = Union("test",
                       ("a", unsigned_char),
                       ("b", unsigned_short))
    
    # Check the type looks sensible (more fully tested by the ComplexType tests)
    assert union_test.name == "union test"
    assert union_test.native == False
    assert union_test.prototype == "union test;"
    assert union_test.definition == ("union test {\n"
                                      "    unsigned char a;\n"
                                      "    unsigned short b;\n"
                                      "};")
    assert union_test.declare() == ("union test")
    assert union_test.declare("magic") == ("union test magic")
    assert list(union_test.iter_types()) == [unsigned_char,
                                             unsigned_short,
                                             union_test]
    assert repr(union_test) == "<Union: union test>"
    
    # Check the instances look sensible (again, the ComplexTypeInstance base
    # class is more fully tested elsewhere)
    t = union_test(unsigned_char(123))
    assert isinstance(t, UnionInstance)
    assert t.a.value == 123
    assert t.b.value == 123
    assert t.data_type == union_test
    assert t.size == 2
    assert t.literal == ("(union test){\n"
                         "    123,\n"
                         "    123\n"
                         "}")
    assert str(t) == "{a: 123, b: 123}"
    assert repr(t) == "<union test: {a: 123, b: 123}>"
    
    # Should be able to change the address which should change all members
    # addresses too
    assert t.address is None
    t.address = 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1000
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
    t.b.address = 0x1000
    assert t.address == 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1000
    
    # Should get an error if the address is changed erroneously
    with pytest.raises(ValueError):
        t.a.address = 0xFFFF
    with pytest.raises(ValueError):
        t.b.address = 0xFFFF
    assert t.address == 0x1000
    assert t.a.address == 0x1000
    assert t.b.address == 0x1000
    
    # Should be able to set an instance and its address should be updated
    new_a = unsigned_char(t.a.value)
    new_a.address = 0xDEADBEEF
    t.a = new_a
    assert new_a.address == 0x1000
    
    t.address = None
    with pytest.raises(ValueError):
        t.a.address = 0xFFFF
    with pytest.raises(ValueError):
        t.b.address = 0xFFFF
    assert t.address is None
    assert t.a.address is None
    assert t.b.address is None
    
    # Packing should work (with default endianness)
    assert t.pack() == b"{\0"
    
    # Unpacking should too
    t = union_test()
    t.unpack(b"\xFF\xAA")
    assert t.a.value == 0xFF
    assert t.b.value == 0xAAFF


@pytest.mark.parametrize("endianness,a,b,"
                         "just_a_b_value,just_b_a_value,"
                         "a_then_b_a_value,b_then_a_a_value,"
                         "a_then_b_b_value,b_then_a_b_value",
                         [(Endianness.little, 0xAA, 0xBBCC,
                           0x00AA, 0xCC,
                           0xCC, 0xAA,
                           0xBBCC, 0xBBAA),
                          (Endianness.big, 0xAA, 0xBBCC,
                           0xAA00, 0xBB,
                           0xBB, 0xAA,
                           0xBBCC, 0xAACC)])
def test_union_behaviour(endianness, a, b,
                         just_a_b_value, just_b_a_value,
                         a_then_b_a_value, b_then_a_a_value,
                         a_then_b_b_value, b_then_a_b_value):
    union_test = Union("test",
                        ("a", unsigned_char),
                        ("b", unsigned_short),
                        endianness=endianness)
    
    # Default value should be zero
    t = union_test()
    assert t.a.value == 0
    assert t.b.value == 0
    
    # Should be able to set just a
    t = union_test(unsigned_char(a))
    assert t.a.value == a
    assert t.b.value == just_a_b_value
    
    t = union_test(a=unsigned_char(a))
    assert t.a.value == a
    assert t.b.value == just_a_b_value
    
    t = union_test()
    t.a.value = a
    assert t.a.value == a
    assert t.b.value == just_a_b_value
    
    # Should be able to set just b
    t = union_test(b=unsigned_short(b))
    assert t.a.value == just_b_a_value
    assert t.b.value == b
    
    t = union_test()
    t.b.value = b
    assert t.a.value == just_b_a_value
    assert t.b.value == b
    
    # Shouldn't be able to initialise both
    with pytest.raises(ValueError):
        union_test(unsigned_char(a), unsigned_short(b))
    with pytest.raises(ValueError):
        union_test(unsigned_char(a), b=unsigned_short(b))
    with pytest.raises(ValueError):
        union_test(a=unsigned_char(a), b=unsigned_short(b))
    
    
    # Should be able to set a then b
    t = union_test(unsigned_char(a))
    t.b.value = b
    assert t.a.value == a_then_b_a_value
    assert t.b.value == a_then_b_b_value
    
    t = union_test(a=unsigned_char(a))
    t.b.value = b
    assert t.a.value == a_then_b_a_value
    assert t.b.value == a_then_b_b_value
    
    t = union_test()
    t.a.value = a
    t.b.value = b
    assert t.a.value == a_then_b_a_value
    assert t.b.value == a_then_b_b_value
    
    t = union_test()
    t.a = unsigned_char(a)
    t.b = unsigned_short(b)
    assert t.a.value == a_then_b_a_value
    assert t.b.value == a_then_b_b_value
    
    # Should be able to set b then a
    t = union_test(b=unsigned_short(b))
    t.a.value = a
    assert t.a.value == b_then_a_a_value
    assert t.b.value == b_then_a_b_value
    
    t = union_test()
    t.b.value = b
    t.a.value = a
    assert t.a.value == b_then_a_a_value
    assert t.b.value == b_then_a_b_value
    
    t = union_test()
    t.b = unsigned_short(b)
    t.a = unsigned_char(a)
    assert t.a.value == b_then_a_a_value
    assert t.b.value == b_then_a_b_value
    
    # Should fail to pack/unpack with the wrong-endianness
    for wrong_endianness in Endianness:
        if wrong_endianness != endianness:
            with pytest.raises(ValueError):
                t.pack(endianness=wrong_endianness)
            
            packed_data = t.pack(endianness=endianness)
            with pytest.raises(ValueError):
                t.unpack(packed_data, endianness=wrong_endianness)


def test_container():
    union_test = Union("test",
                        ("a", unsigned_char),
                        ("b", unsigned_short))
    s = union_test()
    
    container = Mock()
    s._parents.append(container)
    
    # Changing the address should cause a callback
    s.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(s)
    container._child_address_changed.reset_mock()
    
    # Changing a union member's address shouldn't
    s.a.address = 0xDEADBEEF
    assert not container._child_address_changed.called
    
    # Changing a union member's value should cause a callback 
    s.a.value = 123
    container._child_value_changed.assert_called_once_with(s)
    container._child_value_changed.reset_mock()
    
    # As should changing the instance
    s.a = unsigned_char()
    container._child_value_changed.assert_called_once_with(s)
    container._child_value_changed.reset_mock()
    
    # As should unpacking
    s.unpack(b"\0\0")
    container._child_value_changed.assert_called_once_with(s)
    container._child_value_changed.reset_mock()


def test_nested():
    # Ensure that nested unions can be initialised
    union_inner = Union("inner",
                        ("a", unsigned_char),
                        ("b", unsigned_short))
    union_outer = Union("outer",
                        ("a", unsigned_char),
                        ("b", union_inner))
    
    # Default constructor should work
    t = union_outer()
    assert t.a.value == 0
    assert t.b.a.value == 0
    assert t.b.b.value == 0
    
    # Single initialiser should work
    t = union_outer(unsigned_char(123))
    assert t.a.value == 123
    assert t.b.a.value == 123
    assert t.b.b.value == 123
    
    t = union_outer(a=unsigned_char(123))
    assert t.a.value == 123
    assert t.b.a.value == 123
    assert t.b.b.value == 123
    
    t = union_outer(b=union_inner(unsigned_char(123)))
    assert t.a.value == 123
    assert t.b.a.value == 123
    assert t.b.b.value == 123
    
    # Nested initialisers should work
    t = union_outer(b__a=unsigned_char(123))
    assert t.a.value == 123
    assert t.b.a.value == 123
    assert t.b.b.value == 123
    
    t = union_outer(b__b=unsigned_short(0xAABB))
    assert t.a.value == 0xBB
    assert t.b.a.value == 0xBB
    assert t.b.b.value == 0xAABB
    
    # Should fail to initialise a nested union more than once
    with pytest.raises(ValueError):
        union_outer(b=union_inner(unsigned_char(123)),
                    b__a=unsigned_char(123))
