"""Utility functions used internally by the cdata module."""

def indent(string, indentation="    ", indent_empty_lines=False):
    """Indent a multi-line string using the given indentation characters.
    
    Parameters
    ----------
    string : str
        The (possibly multi-line) string to be indented.
    indentation : str
        The string to be prepended to every line in order to indent it. Defaults
        to four spaces.
    indent_empty_lines : bool
        Should empty lines be indented? Defaults to False.
    
    Returns
    -------
    str
        The input string, indented by the specified amount.
    """
    
    return "\n".join("{}{}".format((indentation if line or indent_empty_lines
                                    else ""),
                                   line)
                     for line in string.split("\n"))


class EmptyIterable(object):
    """An object which when iterated over, iterates over the empty list."""
    
    def __iter__(self):
        return iter([])

empty_iterable = EmptyIterable()


def char_literal(value):
    """Render a char as a C literal."""
    
    value = int(value[0])
    if value < 128:
        if value == ord("'"):
            # Special case: needs escaping
            return "'\\''"
        else:
            return "'{}'".format(repr(chr(value))[1:-1])
    else:
        return "'\\x{:02x}'".format(value)
