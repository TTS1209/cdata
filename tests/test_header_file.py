import pytest

import time

from cdata.enum import Enum

from cdata.struct import Struct

from cdata.primitive import char

from cdata.header_file import to_header

def test_empty():
    # Shouldn't fail on an empty list of types
    to_header()


def test_simple_types():
    # Simple types shouldn't appear in the header
    assert "char" not in to_header(char)


def test_prototype_free():
    # Types without prototypes should just have their specifications listed
    my_enum = Enum("my_enum", ("Magic", None))
    
    assert my_enum.prototype == ""
    assert my_enum.definition != ""
    assert my_enum.definition in to_header(my_enum)


def test_ordering():
    # When multiple types are supplied, the first type should be listed first,
    # etc.
    my_structs = [Struct("my_struct{}".format(n)) for n in range(10)]
    
    header = to_header(*my_structs)
    
    # Make sure the prototypes/defintions are unique
    assert len(set(s.prototype for s in my_structs)) == len(my_structs)
    assert len(set(s.definition for s in my_structs)) == len(my_structs)
    
    # Check all the prototypes appear (and that the definitions appear after all
    # the prototypes)
    assert all(s.prototype in header for s in my_structs)
    after_prototypes = header.partition(my_structs[-1].prototype)[2]
    assert all(s.definition in after_prototypes for s in my_structs)


def test_nested_types():
    # When types reference other types, those referenced types should be
    # included (and included in the correct order).
    struct_inner = Struct("inner")
    struct_outer = Struct("outer", ("inner", struct_inner))
    
    # Shouldn't include things which aren't needed
    header = to_header(struct_inner)
    assert struct_outer.definition not in header
    assert struct_inner.definition in header
    
    # Both should be included when the outer struct is specified (and the outer
    # struct should be specified last)
    header = to_header(struct_outer)
    assert struct_inner.definition in header
    after_inner = header.partition(struct_inner.definition)[2]
    assert struct_outer.definition in after_inner


def test_omit_native():
    # Types marked as native should not be included
    my_native_struct = Struct("my_native_struct", native=True)
    assert "struct my_native_struct" not in to_header(my_native_struct)
    
    # Should be included when omit_native is disabled
    assert "struct my_native_struct" in to_header(my_native_struct,
                                                  omit_native=False)


def test_header_guards():
    # Should have header guards by default.
    assert "\n#ifndef " in to_header()
    assert "\n#define " in to_header()
    assert to_header().endswith("\n#endif")
    
    # Header guards should be given long-ish unique names if unspecified
    guard_id0 = to_header().partition("\n#define")[2].partition("\n")[0]
    guard_id1 = to_header().partition("\n#define")[2].partition("\n")[0]
    assert len(guard_id0) > 10
    assert guard_id0 != guard_id1
    
    # If a specific header guard name is supplied, that should be used
    header = to_header(include_header_guards="MY_HEADER_H")
    guard_id = header.partition("\n#define ")[2].partition("\n")[0]
    assert guard_id == "MY_HEADER_H"
    assert "#ifndef MY_HEADER_H\n#define MY_HEADER_H" in header
    assert header.endswith("\n#endif")
    
    # If header guards are disabled, they should be omitted
    header = to_header(include_header_guards=False)
    assert "#ifndef " not in header
    assert "#define " not in header
    assert not header.endswith("#endif")


def test_timestamp():
    # The top of the file should have a timestamp
    h0 = to_header(include_header_guards=False)
    time.sleep(0.01)
    h1 = to_header(include_header_guards=False)
    
    assert h0.partition("#ifndef")[0] != h1.partition("#ifndef")[0]


def test_doc():
    # The documentation message should be included in a comment
    assert "* Hello, world!" in to_header(doc="Hello, world!")


def test_includes():
    # The Include lines should be included after the header guards
    header = to_header(includes="#include <sys.h>")
    _, _, after_include_guards = header.partition("#define ")
    assert "\n#include <sys.h>\n" in after_include_guards
