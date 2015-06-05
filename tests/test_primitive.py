import pytest

from mock import Mock

from cdata import primitive

from cdata.endianness import Endianness


class TestPrimitive(object):
    """Test the basic functions of the Primitive type."""
    
    def test_default_args(self):
        """Ensure that the primitive data type applies its arguments
        correctly."""
        test_t = primitive.Primitive("test_t", "B", cast=(lambda v: v),
                                     default_value=123)
        assert test_t.name == "test_t"
        assert test_t.native == False
        assert test_t.prototype == ""
        assert test_t.definition == ""
        assert test_t.declare() == "test_t"
        assert test_t.declare("magic") == "test_t magic"
        assert test_t.struct_format == "B"
        assert test_t.default_value == 123
        assert list(test_t.iter_types()) == [test_t]
        assert repr(test_t) == "<Primitive: test_t>"
        
        # Instances should be created accordingly
        inst = test_t()
        assert inst.data_type is test_t
        assert inst.address is None
        assert inst.value == 123
        assert inst.size == 1
        assert inst.literal == "123"
        assert inst.pack() == b"\x7B"
        inst.unpack(b"\xAB")
        assert inst.value == 171
        assert str(inst) == "171"
        assert repr(inst) == "<test_t: 171>"
    
    def test_cast(self):
        """Ensure the cast argument is used."""
        test_t = primitive.Primitive("test_t", "B", default_value=0,
                                     cast=(lambda v: v + 1))
        inst = test_t(123)
        assert inst.value == 124  # 123 + 1 due to cast
    
    def test_to_literal(self):
        """Ensure the to_literal argument is used."""
        test_t = primitive.Primitive("test_t", "B", default_value=123,
                                     cast=(lambda v: v),
                                     to_literal=(lambda v: "hi {}".format(v)))
        inst = test_t()
        assert inst.literal == "hi 123"
    
    @pytest.mark.parametrize("native", [True, False])
    def test_native(self, native):
        """Ensure the native argument is used."""
        test_t = primitive.Primitive("test_t", "B", default_value=123,
                                     cast=(lambda v: v),
                                     native=native)
        assert test_t.native == native
    
    def test_container(self):
        """Ensure any container is called whenever the value changes."""
        test_t = primitive.Primitive("test_t", "B", default_value=123,
                                     cast=(lambda v: v))
        inst = test_t()
        
        container = Mock()
        inst._parents.append(container)
        
        # Reading the address should not call the callback
        inst.address
        assert not container._child_address_changed.called
        
        # Changing the address should call the callback
        inst.address = 0xDEADBEEF
        container._child_address_changed.assert_called_once_with(inst)
        container._child_address_changed.reset_mock()
        
        inst.address = None
        container._child_address_changed.assert_called_once_with(inst)
        container._child_address_changed.reset_mock()
        
        # Reading the value should do nothing
        inst.value
        assert not container._child_value_changed.called
        
        # Packing the value should do nothing
        inst.pack()
        assert not container._child_value_changed.called
        
        # Setting the value should call the callback
        inst.value = 0
        container._child_value_changed.assert_called_once_with(inst)
        container._child_value_changed.reset_mock()
        
        # Unpacking the value should call the callback
        inst.unpack(b"\xFF")
        container._child_value_changed.assert_called_once_with(inst)
        container._child_value_changed.reset_mock()


class TestStandardTypes(object):
    """Test the standard C primitive types."""
    
    def test_char(self):
        # Type properties
        assert primitive.char.name == "char"
        assert primitive.char.native == True
        assert primitive.char.prototype == ""
        assert primitive.char.definition == ""
        assert primitive.char.declare() == "char"
        assert primitive.char.declare("magic") == "char magic"
        
        # Test defaults
        c = primitive.char()
        assert c.value == b"\x00"
        assert c.size == 1
        assert c.literal == "'\\x00'"
        
        # Test pack/unpack
        assert c.pack() == b"\x00"
        c.unpack(b"t")
        assert c.value == b"t"
        assert c.pack() == b"t"
        
        # Test setting values
        assert primitive.char(b"a").value == b"a"
        assert primitive.char(b"\x00").value == b"\x00"
        assert primitive.char(b"\xFF").value == b"\xFF"
        
        # Should be able to set from integers too
        assert primitive.char(0xFF).value == b"\xFF"
        
        # Test C literal representation
        assert primitive.char(b"a").literal == "'a'"
        assert primitive.char(b"\0").literal == "'\\x00'"
        assert primitive.char(b"\n").literal == "'\\n'"
        assert primitive.char(b"\xFF").literal == "'\\xff'"
    
    def test__Bool(self):
        # Type properties
        assert primitive._Bool.name == "_Bool"
        assert primitive._Bool.native == True
        assert primitive._Bool.prototype == ""
        assert primitive._Bool.definition == ""
        assert primitive._Bool.declare() == "_Bool"
        assert primitive._Bool.declare("magic") == "_Bool magic"
        
        # Test defaults
        b = primitive._Bool()
        assert b.value == False
        assert b.size == 1
        assert b.literal == "0"
        
        # Test pack/unpack
        assert b.pack() == b"\x00"
        b.unpack(b"\x11")
        assert b.value == True
        assert b.pack() == b"\x01"
        
        # Test setting values
        assert primitive._Bool(False).value == False
        assert primitive._Bool(True).value == True
        
        # Test b literal representation
        assert primitive._Bool(True).literal == "1"
        assert primitive._Bool(1).literal == "1"
        assert primitive._Bool(2).literal == "1"
        assert primitive._Bool(False).literal == "0"
        assert primitive._Bool(0).literal == "0"
    
    @pytest.mark.parametrize("data_type,name,signed,n_bits",
                             [(primitive.signed_char,
                               "signed char", True, 8),
                              (primitive.unsigned_char,
                               "unsigned char", False, 8),
                              (primitive.short,
                               "short", True, 16),
                              (primitive.unsigned_short,
                               "unsigned short", False, 16),
                              (primitive.int,
                               "int", True, 32),
                              (primitive.unsigned_int,
                               "unsigned int", False, 32),
                              (primitive.long,
                               "long", True, 32),
                              (primitive.unsigned_long,
                               "unsigned long", False, 32),
                              (primitive.long_long,
                               "long long", True, 64),
                              (primitive.unsigned_long_long,
                               "unsigned long long", False, 64),
                             ])
    def test_integer_types(self, data_type, name, signed, n_bits):
        """Generic tests for native integer types."""
        n_bytes = n_bits // 8
        
        # Type properties
        assert data_type.name == name
        assert data_type.native == True
        assert data_type.prototype == ""
        assert data_type.definition == ""
        assert data_type.declare() == name
        assert data_type.declare("magic") == "{} magic".format(name)
        
        # Test defaults
        i = data_type()
        assert i.value == 0
        assert i.size == n_bytes
        assert i.literal == "0"
        
        # Test pack/unpack ignoring endianness
        assert i.pack() == b"\x00" * n_bytes
        i.unpack(b"\x12" * n_bytes)
        assert i.value == sum(0x12 << n for n in range(0, n_bits, 8))
        assert i.pack() == b"\x12" * n_bytes
        
        # Test unpack little-endian
        i = data_type(sum(n << n for n in range(0, n_bits, 8)))
        assert i.pack(endianness=Endianness.little) == \
            b"".join(bytes([n]) for n in range(0, n_bits, 8))
        
        # Test pack little-endian
        data = b"".join(bytes([n * 2]) for n in range(0, n_bits, 8))
        i.unpack(data, endianness=Endianness.little)
        assert i.value == sum((n * 2) << n for n in range(0, n_bits, 8))
        
        # Test unpack big-endian
        i = data_type(sum(n << n for n in range(0, n_bits, 8)))
        assert i.pack(endianness=Endianness.big) == \
            b"".join(bytes([n]) for n in reversed(range(0, n_bits, 8)))
        
        # Test pack big-endian
        data = b"".join(bytes([n * 2]) for n in reversed(range(0, n_bits, 8)))
        i.unpack(data, endianness=Endianness.big)
        assert i.value == sum((n * 2) << n for n in range(0, n_bits, 8))
        
        
        # Test setting values also casts them appropriately
        big_positive = (1 << (n_bits - 1)) - 1
        big_negative = -1 << (n_bits - 1)
        big_negative_w = big_negative & ((1 << n_bits) - 1)
        assert data_type(big_positive).value == big_positive
        if signed:
            assert data_type(big_negative).value == big_negative
        else:
            assert data_type(big_negative).value == big_negative_w
        
        # Test C literal representation
        assert data_type(big_positive).literal == str(big_positive)
        if signed:
            assert data_type(big_negative).literal == str(big_negative)
        else:
            assert data_type(big_negative).literal == str(big_negative_w)
    
    @pytest.mark.parametrize("data_type,name,n_bits",
                             [(primitive.float, "float", 32),
                              (primitive.double, "double", 64),
                             ])
    def test_float_types(self, data_type, name, n_bits):
        """Generic tests for native float types."""
        n_bytes = n_bits // 8
        
        # Type properties
        assert data_type.name == name
        assert data_type.native == True
        assert data_type.prototype == ""
        assert data_type.definition == ""
        assert data_type.declare() == name
        assert data_type.declare("magic") == "{} magic".format(name)
        
        # Test defaults
        f = data_type()
        assert f.value == 0.0
        assert f.size == n_bytes
        assert f.literal == "0.0"
        
        for value in [0.0, 0.5, 1.0, -0.5, -1.0]:
            # Test value setting
            f = data_type(value)
            assert f.value == value
            
            # Test pack/unpack
            for endianness in Endianness:
                packed = f.pack(endianness=endianness)
                assert len(packed) == n_bytes
                f.unpack(packed, endianness=endianness)
                assert f.value == value
            
            # Test C literals
            assert f.literal == str(value)
