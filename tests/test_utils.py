from cdata.utils import indent, empty_iterable


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
