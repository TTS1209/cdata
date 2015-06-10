from mock import Mock

from cdata.padding import Padding, PaddingInstance

from cdata.union import Union

from cdata.primitive import unsigned_char, unsigned_short

from mock_container import container

def test_padding_type():
    pad2 = Padding(2)
    
    # Test the underlying type's representation looks OK
    assert pad2.name == "char[2]"
    assert pad2.native == True
    assert pad2.prototype == ""
    assert pad2.definition == ""
    assert pad2.declare() == "char[2]"
    assert pad2.declare("magic") == "char magic[2]"
    assert list(pad2.iter_types()) == [pad2]
    assert repr(pad2) == "<Padding: char[2]>"
    
    # Test instances do too
    p = pad2()
    assert isinstance(p, PaddingInstance)
    assert p.data_type is pad2
    assert p.address is None
    assert p.size == 2
    assert p.literal == "{'\\x00', '\\x00'}"
    assert list(p.iter_instances()) == [p]
    assert str(p) == "b'\\x00\\x00'"
    assert repr(p) == "<char[2]: b'\\x00\\x00'>"
    
    assert p.pack() == b"\x00\x00"
    
    # If a value is unpacked into the padding value, it should be remembered
    p.unpack(b"\xAA\xBB")
    assert p.pack() == b"\xAA\xBB"
    assert str(p) == "b'\\xaa\\xbb'"

def test_parent(container):
    # Check the container is informed when the padding bytes change and when the
    # address changes.
    pad2 = Padding(2)
    
    p = pad2()
    referrer = Mock()
    p._container = container
    p._referrer = referrer
    
    assert not container._child_value_changed.called
    assert not referrer._child_value_changed.called
    p.unpack(b"AB")
    container._child_value_changed.assert_called_once_with(p)
    referrer._child_value_changed.assert_called_once_with(p)
    
    assert not container._child_address_changed.called
    assert not referrer._child_address_changed.called
    p.address = 0xDEADBEEF
    container._child_address_changed.assert_called_once_with(p)
    referrer._child_address_changed.assert_called_once_with(p)
    
    # Check iteration lists only the container
    assert list(p.iter_instances()) == [container]
