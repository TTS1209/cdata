import pytest

from mock import Mock

from cdata.enum import Enum, EnumInstance

from cdata.endianness import Endianness

def test_enum_named():
    # Test the basic data type features work as expected for named enums.
    my_enum = Enum("my_enum",
                   ("ONE", 1),
                   ("TWO", 2),
                   ("THREE", 3))
    
    assert my_enum.name == "enum my_enum"
    assert my_enum.native == False
    assert my_enum.prototype == "enum my_enum;"
    assert my_enum.definition == ("enum my_enum {\n"
                                  "    ONE = 1,\n"
                                  "    TWO = 2,\n"
                                  "    THREE = 3\n"
                                  "};")
    assert my_enum.declare() == "enum my_enum"
    assert my_enum.declare("magic") == "enum my_enum magic"
    assert list(my_enum.iter_types()) == [my_enum]
    assert repr(my_enum) == "<Enum: enum my_enum>"


def test_enum_anonymous():
    # Test the basic data type features work as expected for named enums.
    my_enum = Enum(("ONE", 1),
                   ("TWO", 2),
                   ("THREE", 3))
    
    assert my_enum.name == ("enum {\n"
                            "    ONE = 1,\n"
                            "    TWO = 2,\n"
                            "    THREE = 3\n"
                            "}")
    assert my_enum.native == False
    assert my_enum.prototype == ""
    assert my_enum.definition == ""
    assert my_enum.declare() == ("enum {\n"
                                 "    ONE = 1,\n"
                                 "    TWO = 2,\n"
                                 "    THREE = 3\n"
                                 "}")
    assert my_enum.declare("magic") == ("enum {\n"
                                        "    ONE = 1,\n"
                                        "    TWO = 2,\n"
                                        "    THREE = 3\n"
                                        "} magic")
    assert list(my_enum.iter_types()) == [my_enum]
    assert repr(my_enum) == ("<Enum: enum {\n"
                             "    ONE = 1,\n"
                             "    TWO = 2,\n"
                             "    THREE = 3\n"
                             "}>")


def test_automatic():
    # Test that enum members can be automatically given values
    my_enum = Enum("my_enum",
                   ("ZERO", None),
                   ("ONE", None),
                   ("TWO", None))
    assert my_enum.definition == ("enum my_enum {\n"
                                  "    ZERO = 0,\n"
                                  "    ONE = 1,\n"
                                  "    TWO = 2\n"
                                  "};")
    
    # Ensure the counts can be started from a specified value
    my_enum = Enum("my_enum",
                   ("ONE", 1),
                   ("TWO", None),
                   ("THREE", None))
    assert my_enum.definition == ("enum my_enum {\n"
                                  "    ONE = 1,\n"
                                  "    TWO = 2,\n"
                                  "    THREE = 3\n"
                                  "};")
    
    # Ensure the counts can be re-started
    my_enum = Enum("my_enum",
                   ("ONE", 1),
                   ("TWO", None),
                   ("FOUR", 4))
    assert my_enum.definition == ("enum my_enum {\n"
                                  "    ONE = 1,\n"
                                  "    TWO = 2,\n"
                                  "    FOUR = 4\n"
                                  "};")


@pytest.mark.parametrize("name", ["_underscore_at_start",
                                  "name",
                                  "native",
                                  "declare"])
def test_reserved_enum_names(name):
    # Test that various enum value names are not allowed
    with pytest.raises(ValueError):
        Enum((name, 0))


def test_duplicate_enum_names():
    # Test that defining an enum name multiple times fails
    with pytest.raises(ValueError):
        Enum(("XXX", 0), ("XXX", 1))


def test_duplicate_enum_values():
    # Test that defining an enum with a value used more than once fails
    with pytest.raises(ValueError):
        Enum(("XXX", 0), ("YYY", 0))


def test_duplicate_enum_value_bad_type():
    # Test that defining an enum with an unsupported type fails.
    with pytest.raises(ValueError):
        Enum(("XXX", 0.5))


@pytest.mark.parametrize("n_bits,packed",
                         [(8, b"\x01"),
                          (16, b"\x01\0"),
                          (32, b"\x01\0\0\0"),
                          (64, b"\x01\0\0\0\0\0\0\0")])
def test_sizes(n_bits, packed):
    # Test that different sizes are allowed.
    
    # Test enum value bounds checking
    with pytest.raises(ValueError):
        Enum(("XXX", 1 << n_bits), enum_size=n_bits)
    with pytest.raises(ValueError):
        Enum(("XXX", -1), enum_size=n_bits)
    
    my_enum = Enum(("ONE", 1), enum_size=n_bits)
    
    # Test pack/unpack
    e = my_enum()
    assert e.pack() == packed
    e.unpack(packed)
    assert e.value == "ONE"


def test_bad_size():
    # Test that unsupported sizes fail early
    with pytest.raises(ValueError):
        Enum(("XXX", 1), enum_size=48)


def test_enum_instance():
    # Test that instances of enums behave correctly.
    my_enum = Enum("my_enum",
                   ("ONE", 1),
                   ("TWO", 2),
                   ("THREE", 3))
    
    # Basic API
    e = my_enum()
    assert isinstance(e, EnumInstance)
    assert e.data_type is my_enum
    assert e.address is None
    e.address = 0xDEADBEEF
    assert e.address is 0xDEADBEEF
    assert e.size == 4
    assert e.literal == "ONE"
    assert str(e) == "ONE"
    assert repr(e) == "<enum my_enum: ONE>"
    
    # Packing
    assert e.pack() == b"\x01\0\0\0"
    assert e.pack(Endianness.little) == b"\x01\0\0\0"
    assert e.pack(Endianness.big) == b"\0\0\0\x01"
    
    # Unpacking
    e.unpack(b"\x02\0\0\0")
    assert e.value == "TWO"
    e.unpack(b"\0\0\0\x01", Endianness.big)
    assert e.value == "ONE"
    e.unpack(b"\x03\0\0\0", Endianness.little)
    assert e.value == "THREE"
    
    # Unpacking an out-of-range value should fail (and not change the value)
    e.value = "THREE"
    with pytest.raises(ValueError):
        e.unpack(b"\0\0\0\0")
    assert e.value == "THREE"
    
    # Assignment should work
    e.value = "TWO"
    assert e.value == "TWO"
    assert e.pack() == b"\x02\0\0\0"
    
    # Instantiation by name should work
    e = my_enum("THREE")
    assert e.value == "THREE"
    assert e.pack() == b"\x03\0\0\0"
    
    # Instantiation by attribute should work
    e = my_enum.TWO
    assert e.value == "TWO"
    assert e.pack() == b"\x02\0\0\0"
    
    # Instantiation by attribute should produce a new instance every time
    assert my_enum.THREE is not my_enum.THREE
    
    # Should not be able to instantiate non-existant enumeration values
    with pytest.raises(ValueError):
        my_enum("FOUR")
    
    # Shouldn't be able to assign them either
    with pytest.raises(ValueError):
        e.value = "FOUR"


def test_container():
    # Test that enum instances inform their container when changed
    my_enum = Enum("my_enum",
                   ("ONE", 1),
                   ("TWO", 2),
                   ("THREE", 3))
    
    e = my_enum()
    container = Mock()
    e._parents.append(container)
    
    # Assignment should trigger a callback
    e.value = "TWO"
    container._child_value_changed.assert_called_once_with(e)
    container._child_value_changed.reset_mock()
    
    # Unpacking should trigger a callback
    e.unpack(b"\x01\0\0\0")
    container._child_value_changed.assert_called_once_with(e)
    container._child_value_changed.reset_mock()
    
    # Changing address should trigger a callback
    e.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(e)
    container._child_address_changed.reset_mock()
