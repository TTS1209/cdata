cdata: 'struct' for more complex structures
===========================================

**This project is lacking polish and should be considered
unstable/experimental.**

The cdata module is a Python library which allows the definition of C
data structures such as structs, unions, enums and pointers in Python. These
data structures can then be packed and unpacked into a C-compatible memory
layout. Matching structure definitions can also be automatically generated in a
C header file.

Example
-------

```python
>>> import cdata

>>> # Lets make an int!
>>> my_int = cdata.int()
>>> my_int
<int: 0>
>>> my_int.value = 1234
>>> my_int
<int: 1234>

>>> # Now lets define a new type of struct called `struct foo`
>>> struct_foo = cdata.Struct("foo",
>>>                           ("bar", cdata.int),
>>>                           ("baz", cdata.Pointer(cdata.char)))
>>> # We can see the C definition like so:
>>> struct_foo.definition
struct foo {
    int bar;
    char* baz;
};

>>> # Now lets create an instance of that struct.
>>> my_foo = struct_foo(bar=cdata.int(1234))

>>> # Notice that any fields we didn't specify have a default value (in the case
>>> # of the pointer, just NULL)
>>> my_foo
<struct foo: {bar: 1234, baz: NULL}>

>>> # We can, of course, easily change fields
>>> my_foo.bar.value = 42
>>> # Including the pointer!
>>> c = cdata.char(b"H")
>>> my_foo.baz.deref = c
>>> my_foo
<struct foo: {bar: 42, baz: b'H'}>

>>> # But wait, how are addresses chosen? Initially they're not!
>>> my_foo.address
None
>>> c.address
None
>>> # We could set them manually...
>>> #     my_foo.address = 0x1000
>>> #     c.address = 0x1008
>>> # Or we can use the "alloc" utility function to discover all reachable
>>> # instances and assign them non-overlapping addresses.
>>> cdata.alloc(my_foo, 0x2000)
8201
>>> hex(my_foo.address)
'0x2000'
>>> hex(c.address)
'0x2008'

>>> # If we then want to write this into a file we can use the iter_instances
>>> # method of a cdata instance to iterate over all accessible instances and
>>> # then the "pack" method to generate the packed representation of the
>>> # structure.
>>> for instance in my_foo.iter_instances():
...     f.seek(instance.address)
...     f.write(instance.pack())
```
