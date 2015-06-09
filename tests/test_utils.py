import pytest

from cdata.utils import \
    indent, comment, comment_wrap, empty_iterable, char_literal


def test_indent():
    # By default it should not indent a single empty line
    assert indent("") == ""
    
    # ...unless forced
    assert indent("", indent_empty_lines=True) == "    "
    assert indent("", indentation="\t", indent_empty_lines=True) == "\t"
    
    # Should indent a non-empty line
    assert indent("Hello, World!") == "    Hello, World!"
    assert indent("Hello, World!", indentation="\t") == "\tHello, World!"
    
    # Should indent several lines
    assert indent("Hello, World!\n"
                  "How are you?") == ("    Hello, World!\n"
                                      "    How are you?")
    assert indent("Hello, World!\n"
                  "How are you?",
                  indentation="\t") == ("\tHello, World!\n"
                                        "\tHow are you?")
    
    # Should skip blank lines
    assert indent("Hello, World!\n"
                  "\n"
                  "How are you?") == ("    Hello, World!\n"
                                      "\n"
                                      "    How are you?")
    
    # ...unless told otherwise
    assert indent("Hello, World!\n"
                  "\n"
                  "How are you?",
                  indent_empty_lines=True) == ("    Hello, World!\n"
                                               "    \n"
                                               "    How are you?")

def test_comment():
    # Special case: empty comment
    assert comment("")  == ("/* */")
    
    # Single line comment
    assert comment("One-liner!")  == ("/* One-liner! */")
    
    # Multi-line comment
    assert comment("Two-\nliner!")  == ("/* Two-\n"
                                        " * liner! */")
    
    # Empty lines should have any excess whitespace trimmed
    assert comment("Empty\n\nLine")  == ("/* Empty\n"
                                         " *\n"
                                         " * Line */")
    
    # Alternative comment style should be possible
    assert comment("Alternative\n\nComment\nStyle", "// ", "// ", "") == \
        ("// Alternative\n"
         "//\n"
         "// Comment\n"
         "// Style")


@pytest.mark.parametrize("string",
    # |-----20 chars-----|
    ["no comment",
     # Empty comments
     "before\n"
     "with /**/\n"
     "after",
    
     "before\n"
     "with /* */\n"
     "after",
    
     "before\n"
     "with /*  */\n"
     "after",
     
     # Single line, non wrapping
     "before\n"
     "with /* no wrap */\n"
     "after",
     
     # Single line, non wrapping with end on own line
     "before\n"
     "with /* no wrap\n"
     "      */\n"
     "after",
     
     # Multi line, non wrapping
     "before\n"
     "with /* no wrap\n"
     "      * for me */\n"
     "after",
    
     # Multi line, non wrapping with end on its own line
     "before\n"
     "with /* no wrap\n"
     "      * for me\n"
     "      */\n"
     "after",
    
     # Multi line, with blank lines
     "before\n"
     "with /*\n"
     "      * no wrap\n"
     "      *\n"
     "      * for me\n"
     "      */\n"
     "after",
    
     # Multi line, with blank lines + trialing spaces
     "before\n"
     "with /* \n"
     "      * no wrap\n"
     "      * \n"
     "      * for me\n"
     "      */\n"
     "after",
    
     # Multiple comments
     "before\n"
     "with /* first */\n"
     "between\n"
     "again /* second */\n"
     "after",
    ])
def test_comment_wrap_nop(string):
    # Test that examples which require no wrapping are left unchanged.
    assert comment_wrap(string, 20) == string


@pytest.mark.parametrize("string",
    # |-----20 chars-----|
    [
     # Single line, wrapping
     "before\n"
     "with /* wrap right now */\n"
     "after",
     
     # Single line, wrapping with end on own line
     "before\n"
     "with /* wrap right now\n"
     "      */\n"
     "after",
     
     # Multi line, wrapping
     "before\n"
     "with /* wrap right now\n"
     "      * wrap again now */\n"
     "after",
    
     # Multi line, wrapping with end on its own line
     "before\n"
     "with /* wrap right now\n"
     "      * wrap again now\n"
     "      */\n"
     "after",
    
     # Multi line, with blank lines
     "before\n"
     "with /*\n"
     "      * wrap right now\n"
     "      *\n"
     "      * wrap again now\n"
     "      */\n"
     "after",
    
     # Multi line, with blank lines + trialing spaces
     "before\n"
     "with /* \n"
     "      * wrap right now\n"
     "      * \n"
     "      * wrap again now\n"
     "      */\n"
     "after",
    
     # Multiple comments
     "before\n"
     "with /* wrap right now */\n"
     "between\n"
     "again /* wrap again now */\n"
     "after",
    ])
def test_comment_wrap(string):
    max_length = 20
    
    # Test that examples which require wrapping are wrapped appropriately
    wrapped = comment_wrap(string, max_length)
    
    # The line wrapping process should only *add* characters (e.g. add
    # whitespace and comment continuations). Check that this is the case.
    wi = 0
    for char in string:
        while wrapped[wi] != char:
            wi += 1
            assert wi < len(wrapped)
    
    # Check that the intended goal of reducing the line-length has been achieved
    for line in wrapped.splitlines():
        assert len(line) < max_length

def test_empty_iterable():
    # The empty iterable should work multiple times!
    for _ in range(10):
        assert list(empty_iterable) == []


def test_char_literal():
    # Printable characters should be represented as literals (just test a random
    # selection
    assert char_literal(b"!") == "'!'"
    assert char_literal(b"a") == "'a'"
    assert char_literal(b"0") == "'0'"
    assert char_literal(b"?") == "'?'"
    assert char_literal(b"\"") == "'\"'"
    
    # Characters which require escaping should be
    assert char_literal(b"'") == "'\\''"
    
    # Common special characters should work
    assert char_literal(b"\n") == "'\\n'"
    assert char_literal(b"\r") == "'\\r'"
    assert char_literal(b"\t") == "'\\t'"
    
    # Non-printable characters should be shown in hex
    assert char_literal(b"\x00") == "'\\x00'"
    assert char_literal(b"\xAA") == "'\\xaa'"
    assert char_literal(b"\xFF") == "'\\xff'"
