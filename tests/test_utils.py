from cdata.utils import indent, empty_iterable, char_literal


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
