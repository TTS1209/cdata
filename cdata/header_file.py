"""Utilities for generating C header files from cdata type definitions."""

import datetime

import uuid

from cdata.base import DataType

from cdata.utils import indent, comment, comment_wrap

def to_header(*types,
              omit_native=True,
              include_header_guards=True,
              doc="", includes="", max_line_width=80):
    """Generate a C header-file which defines a set of cdata types.
    
    Parameters
    ----------
    *types : [:py:class:`cdata.DataType`, ...]
        The types to include in the header. Types will be included recursively
        so if a pariticular data type references another, that other type will
        be included automatically.
    omit_native : bool
        Should types marked as "native" be omitted? (Default: True)
    include_header_guards : bool or str
        Should a header-guard be included? If True, a header guard name will be
        generated from a UUID. If a string, that string will be used as the
        header guard name. If False, no header guard will be included. (Default:
        True)
    doc : str
        An explanatory message to be added to the top of the file. Will be
        automatically wrapped in a C-style comment block and line-wrapped as
        appropriate.
    includes : str
        If any includes are required, these should be povided here (as a literal
        C snippet). These will be inserted before the type definitions but
        within the header guard.
    max_line_width : int or None
        The maximum number of characters to allow on a single line in the output
        code. If not None, the code will be line-wrapped to the specified number
        of characters.
        
        .. note::
            In the current implementation only comment lines will be
            line-wrapped. Future versions may extend this to code blocks too.
    """
    # Accumulate the full set of types
    _generated = set()
    all_types = []
    for type in types:
        all_types.extend(type.iter_types(_generated))
    
    # Omit native types (as required)
    if omit_native:
        all_types = [t for t in all_types if not t.native]
    
    # Build up the header file
    out = ""
    
    # Add user-supplied comment. Note that an extra blank line is inserted after
    # the comment when present to seperate it from the timestamp.
    top_comment = ""
    if doc:
        top_comment += "{}\n\n".format(doc)
    # Add a timestamp
    top_comment += "Automatically generated at {} by cdata.to_header().".format(
        datetime.datetime.now().isoformat())
    
    
    # Add the comment to the output
    out += "{}\n\n".format(comment(top_comment))
    
    # Add the opening header guard (as required)
    if include_header_guards:
        if isinstance(include_header_guards, str):
            guard_name = include_header_guards
        else:
            guard_name = "HEADER_{}".format(uuid.uuid1().hex.upper())
        
        out += "#ifndef {}\n".format(guard_name)
        out += "#define {}\n\n".format(guard_name)
    
    # Add any supplied includes
    if includes:
        out += "{}\n\n".format(includes)
    
    # Add all type prototypes followed by all definitions
    for type in all_types:
        if type.prototype:
            out += "{}\n\n".format(type.prototype)
    for type in all_types:
        if type.definition:
            out += "{}\n\n".format(type.definition)
    
    # Add the closing header guard
    if include_header_guards:
        out += "#endif\n"
    
    # Line-wrap long comments
    out = comment_wrap(out, max_line_width)
    
    return out.rstrip()
