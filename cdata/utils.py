"""Utility functions used internally by the cdata module."""

import re

import textwrap


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

def comment(string, start="/* ", continuation=" * ", end=" */"):
    """Convert the specified string into a multi-line C-style comment.
    
    Parameters
    ----------
    string : str
        The multi-line string to render as a comment.
    start : str
        The prefix which begins a comment.
    continuation : str
        The prefix to add to the start of each additional comment line.
    end : str
        The string to append to the comment to terminate it.
    """
    lines = string.strip().split("\n")
    
    out = ""
    for i, line in enumerate(lines):
        if i == 0:
            this_line = start
        elif i != 0:
            this_line = "\n{}".format(continuation)
        this_line += line
        
        out += this_line.rstrip()
    
    out += end
    
    return out


def comment_wrap(string, max_length=80, tab_width=4,
                 start="/* ", continuation=" * ", end=" */"):
    """Hard-wrap any long comment lines in a supplied string.
    
    .. warning::
        This method is relatively simplistic and thus will get tripped up by
        comments within string literals and when there is more than one comment
        on a line.
    
    .. warning::
        The start, continuation and end arguments must not contain newlines.
    
    Parameters
    ----------
    string : str
        The string to wrap comments in.
    max_length : int
        The maximum length (in characters) of a line in the output.
    tab_width : int
        Number of spaces per tab. Note that this line-wrap function assumes that
        any tabs that appear in the string are strictly the *first* characters
        in a line. (default: 4)
    start : str
        The substring which begins a comment.
    continuation : str
        The substring addded (after any indenting white space) to the start of
        each additional comment line.
    end : str
        The substring which indicates the end of a comment.
    """
    # This algorithm uses a regex to find all comment blocks in the
    # style specified and then works through these comment blocks line-by-line
    # wrapping along long lines.
    
    # The following (multi-line matching) regex matches whole comments of the
    # style specified. Note that variations of the start, continuation and end
    # strings are substituted into the regex with white-space trimmed from
    # various sides.
    comment_regex_src = (r"^.*"  # Lead-up to comment (must be captured so that
                                 # we know the quantity of indentation
                                 # to insert when wrapping this line).
                         r"("
                             # A single-line, empty comment with white space
                             # in the start/end strings possibly omitted.
                             r"({start_}[\t ]*{_end})"
                         r"|"
                             # Single-line, non-empty comment
                             r"({start}[^\n]*{end})"
                         r"|"
                             # A multi-line comment
                             r"("
                                 # First line
                                 r"("
                                     # Non-empty
                                     r"({start}[^\n]*\n)"
                                 r"|"
                                     # If empty, trailing white space from the
                                     # start string may be omitted.
                                     r"({start_}\n)"
                                 r")"
                                 # Continuations
                                 r"("
                                     # Non-empty
                                     r"(\s*{continuation}[^\n]*\n)"
                                 r"|"
                                     # If empty, trailing whitespace in the
                                     # continuation string may be omitted.
                                     r"(\s*{continuation_}\n)"
                                 r")*"
                                 # Final line.
                                 r"("
                                     # Non-empty
                                     r"(\s*{continuation}[^\n]*\s*{end})"
                                 r"|"
                                     # If empty, the continuation need not be
                                     # present, nor any leading white space in
                                     # the end.
                                     r"(\s*{continuation_}?\s*{_end})"
                                 r")"
                             r")"
                         r")").format(start=re.escape(start),
                                      start_=re.escape(start.rstrip()),
                                      
                                      continuation=re.escape(continuation),
                                      continuation_=re.escape(
                                          continuation.rstrip()),
                                      
                                      end=re.escape(end),
                                      _end=re.escape(end.lstrip()),
                                      end_=re.escape(end.rstrip()))
    comment_regex = re.compile(comment_regex_src, re.MULTILINE)
    
    out = ""
    last_char = 0
    
    for m in comment_regex.finditer(string):
        comment_lines = m.group().splitlines()
        
        wrapped_comment_lines = []
        
        for line_no, line in enumerate(comment_lines):
            # We want to break each line into four pieces:
            # * before: the text which precedes the comment on the line
            # * delimiter: the characters which indicates where the comment
            #   begins/continues on the line (e.g. "//", "/* " or " * ").
            # * comment: The text which forms the body of the comment on that
            #   line.
            # * close: The end-of-comment delimiter, if present.
            #
            # To give a concrete example, for a line "abc /* hello */", the
            # parts are:
            # * before: "abc "
            # * delimiter: "/* "
            # * comment: "hello"
            # * close: " */"
            if line_no == 0:
                # On the first line of the comment is started always by the
                # start delimiter (though if the line is empty, it may be
                # started with the start delimiter with trailing whitespace
                # stripped off).
                if start in line:
                    before, delimiter, comment = line.partition(start)
                elif start.rstrip() in line:
                    before, delimiter, comment = line.partition(start.rstrip())
                else:  # pragma: no cover
                    assert False
            else:
                # On other lines, when a continuation is present, the comment
                # continues after that continuation.
                if continuation in line:
                    before, delimiter, comment = line.partition(continuation)
                elif line.endswith(continuation.rstrip()):
                    before, delimiter, comment = line.partition(
                        continuation.rstrip())
                elif end != "" and line.endswith(end):
                    delimiter = ""
                    before, comment, _ = line.partition(end)
                else:  # pragma: no cover
                    assert False
            # Finally, separate out the end-of-comment string if present.
            if comment.endswith(end):
                comment, close, _ = comment.partition(end)
            elif comment.endswith(end.strip()):
                comment, close, _ = comment.partition(end.strip())
            else:
                close = ""
            
            # Work out the sequence of characters required to insert a
            # line-break and comment continuation with matching indent.
            linebreak = "\n{}{}".format(
                # Copy the indentation of the leading text
                "".join(" "*tab_width if c == "\t" else " " for c in before),
                # Followed by a continuation string
                continuation)
            
            # Line-wrap the comment body
            comment_lines = textwrap.wrap(comment,
                                          max_length -
                                              len(before) -
                                              len(delimiter),
                                          break_long_words=False)
            
            # Re-assemble the comment (and any leading text) adding appropriate
            # line-breaks and indentation for each line of the wrapped comment.
            wrapped_comment_lines.append(before +
                                         delimiter +
                                         linebreak.join(comment_lines) +
                                         close)
        
        # Include all text leading up to this comment
        out += string[last_char:m.start()]
        last_char = m.end()
        
        # Include the newly line-wrapped comment
        out += "\n".join(wrapped_comment_lines)
    
    # Include all text after the end of the last comment
    out += string[last_char:]
    
    return out


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
