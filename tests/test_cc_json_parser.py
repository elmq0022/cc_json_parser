from unittest import expectedFailure

import pytest

from cc_json_parser import exceptions as e
from cc_json_parser.cc_json_parser import Parser, not_parsed


@pytest.fixture
def parser():
    def _parser(s):
        p = Parser()
        p.s = s
        p.pos = 0
        return p

    return _parser


@pytest.mark.parametrize(
    "s,expected,error",
    [
        pytest.param("abc", not_parsed, None),
        pytest.param("123", 123, None),
        pytest.param("456", 456, None),
        pytest.param("123 ", 123, None),
        pytest.param(" 123", 123, None),
        pytest.param(" 123   ", 123, None),
        pytest.param("1.23", 1.23, None),
        pytest.param("  1.23", 1.23, None),
        pytest.param("1.23   ", 1.23, None),
        pytest.param("   1.23  ", 1.23, None),
        pytest.param("-1", -1, None),
        pytest.param("1e1", 10, None),
        pytest.param("1e0", 1, None),
        pytest.param("1e+1", 10, None),
        pytest.param("1e-1", 0.1, None),
        pytest.param("1.1e1", 11, None),
        pytest.param("1.1e", None, Exception),
        pytest.param("1.1e-", None, Exception),
        pytest.param("1.1e+", None, Exception),
        pytest.param("1.", 1, None),
        pytest.param("-", None, Exception),
        pytest.param("+", not_parsed, None),
    ],
)
def test_parse_number(parser, s, expected, error):
    p = parser(s)

    try:
        actual = p.parse_number()
    except Exception as e:
        actual = e

    if error:
        assert isinstance(actual, error)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "s,expected,error",
    [
        pytest.param("123", not_parsed, None),
        pytest.param('"abc"', "abc", None),
        pytest.param('"def"', "def", None),
        pytest.param('  "ghi"  ', "ghi", None),
        pytest.param('"\\""', '"', None),
        pytest.param('"\\b"', "\b", None),
        pytest.param('"\\f"', "\f", None),
        pytest.param('"\\n"', "\n", None),
        pytest.param('"\\r"', "\r", None),
        pytest.param('"\\t"', "\t", None),
        pytest.param('"\\uAAAAA"', chr(int("AAAA", 16)), None),
        pytest.param('"\\uAAAAA abc"', chr(int("AAAA", 16)) + " abc", None),
        pytest.param('"abc', None, e.UnmatchedDoubleQuoteException),
        pytest.param(' "abc', None, e.UnmatchedDoubleQuoteException),
        pytest.param('"', None, e.UnmatchedDoubleQuoteException),
    ],
)
def test_parse_double_quoted_string(parser, s, expected, error):
    p = parser(s)

    try:
        actual = p.parse_string()
    except Exception as e:
        actual = e

    if error:
        assert isinstance(actual, error)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "s,expected,error",
    [
        pytest.param("abc", not_parsed, None),
        pytest.param("[]", [], None),
        pytest.param("[    ]", [], None),
        pytest.param("   []", [], None),
        pytest.param("[", None, e.UnmatchedBracketException),
        pytest.param("[   ", None, e.UnmatchedBracketException),
        pytest.param("[123]", [123], None),
        pytest.param('["abc"]', ["abc"], None),
        pytest.param('["abc", "def"]', ["abc", "def"], None),
        pytest.param('["abc", 123]', ["abc", 123], None),
        pytest.param('["abc", "def",]', None, e.TrailingCommaException),
        pytest.param('["abc", "def"   ,   ]', None, e.TrailingCommaException),
        pytest.param('["abc", "def",', None, e.UnmatchedBracketException),
        pytest.param('[ true , false   ,  null ]', [True, False, None], None),
        pytest.param("[1. -]", None, Exception),
    ],
)
def test_parse_array(parser, s, expected, error):
    p = parser(s)

    try:
        actual = p.parse_array()
    except Exception as e:
        actual = e

    if error:
        assert isinstance(actual, error)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "s,expected,error",
    [
        pytest.param("abc", not_parsed, None),
        pytest.param("{}", {}, None),
        pytest.param("{", None, e.UnmatchedBraceException),
        pytest.param("{    ", None, e.UnmatchedBraceException),
        pytest.param('{ "abc":123 }', {"abc": 123}, None),
        pytest.param('{ "abc":123, "def":"ghi" }', {"abc": 123, "def": "ghi"}, None),
        pytest.param('{ "abc":123,}', None, Exception),
        pytest.param('{ "abc":123,  }', None, Exception),
        pytest.param('{"a":123, "a":456}', None, e.DuplicateKeyException),
        pytest.param('{ :"123"}', None, e.InvalidKeyException),
        pytest.param('{"a":', None, e.MissingValueException),
        pytest.param('{"a" 123}', None, e.ExpectedColonException),
        pytest.param('{"a": [1, 2, 3]}', {"a": [1, 2, 3]}, None),
        pytest.param('{"a": {"b":"c"}}', {"a": {"b": "c"}}, None),
        pytest.param('{"a": true}', {"a": True}, None),
        pytest.param('{"a": true }', {"a": True}, None),
        pytest.param('{"a": false }', {"a": False}, None),
        pytest.param('{"a": null }', {"a": None}, None),
    ],
)
def test_parse_object(parser, s, expected, error):
    p = parser(s)

    try:
        actual = p.parse_object()
    except Exception as e:
        actual = e

    if error:
        assert isinstance(actual, error)
    else:
        assert actual == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        pytest.param("true", True),
        pytest.param("true ", True),
        pytest.param("  true ", True),
        pytest.param("bad_keyword", not_parsed),
    ],
)
def test_parse_true(parser, s, expected):
    p = parser(s)
    actual = p.parse_true()
    assert actual == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        pytest.param("false", False),
        pytest.param("false ", False),
        pytest.param("  false ", False),
        pytest.param("bad_keyword", not_parsed),
    ],
)
def test_parse_false(parser, s, expected):
    p = parser(s)
    actual = p.parse_false()
    assert actual == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        pytest.param("null", None),
        pytest.param("null ", None),
        pytest.param("  null ", None),
        pytest.param("bad_keyword", not_parsed),
    ],
)
def test_parse_null(parser, s, expected):
    p = parser(s)
    actual = p.parse_null()
    assert actual == expected


@pytest.mark.parametrize(
    "s,expected",
    [
        pytest.param('', False, id="step 1 - invalid: empty string"),
        pytest.param('{}', True, id="step 1 - valid: empty object"),
        pytest.param('{"key": "value"}', True, id="step 2 - valid: object with key and value"),
        pytest.param('{\n"key": "value",\n"key2": "value"\n}', True, id="step 2 - valid: object with key value pair and whitespace"),
        pytest.param('{"key": "value",}', False, id="step 2 - invalid: object with a trailing comma"),
        pytest.param('{\n"key": "value",\n"key2": value\n}', False, id="step 2 - invalid: object key not double quoted"),
        pytest.param('{\n"key1": true,\n"key2": false,\n"key3": null,\n"key4": "value",\n"key5": 101\n}', True, id="step 3 - valid: object with multiple value types"),
        pytest.param('{\n"key1": true,\n"key2": False,\n"key3": null,\n"key4": "value",\n"key5": 101\n}', False, id="step 3 - invalid: object with a bad keyword False"),
        pytest.param('{\n"key": "value",\n"key-n": 101,\n"key-o": {},\n"key-l": []\n}', True, id="step 4 - valid: object with an empty object and empty list as values"),
        pytest.param('{\n"key": "value",\n"key-n": 101,\n"key-o": {\n"inner key": "inner value"\n},\n"key-l": [\n\'list value\'\n]\n}', False, id="step 4 - invalid: object list item is single quoted"),
        pytest.param('{\n"key": "value",\n"key-n": 101,\n"key-o": {\n"inner key": "inner value"\n},\n"key-l": [\n"list value"\n]\n}', True, id="step 4 - valid: object list item is double quoted"),
    ]
)
def test_challenge_values(parser, s, expected):
    p = parser(s)
    try:
        p.parse(s)
        is_valid = True
    except Exception:
        is_valid = False
    assert is_valid == expected
