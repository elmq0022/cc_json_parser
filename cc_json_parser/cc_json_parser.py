import string

from cc_json_parser import exceptions as e


class NotParsed:
    """
    The single global instance here is a guard value
    return by the specific parsing methods don't
    find anything specific to parse
    """

    ...


NOT_PARSED = NotParsed()


class Parser(object):
    def __init__(self, max_depth=19):
        self.pos = None
        self.s = None
        self.depth = None
        self.max_depth = max_depth

    def current(self):
        return self.s[self.pos]

    def inc(self):
        self.pos += 1
        return self.pos < len(self.s)

    def consume_whitespace(self):
        while self.pos < len(self.s) and self.current() in string.whitespace:
            self.inc()

    def current_is_one_of(self, chars: str):
        if self.pos < len(self.s) and self.current() in chars:
            self.inc()
            return True
        return False

    def get_unicode(self):
        chars = ""
        for _ in range(4):
            if not self.current() in string.hexdigits:
                raise Exception()
            chars += self.current()

            if not self.inc():
                raise e.UnmatchedDoubleQuoteException()

        try:
            result = chr(int(chars, 16))
        except Exception as e:
            raise e

        return result

    def get_digits(self):
        got_digits = False
        while self.pos < len(self.s) and self.current().isnumeric():
            got_digits = True
            self.inc()
        return got_digits

    def parse_number(self):
        self.consume_whitespace()
        if not self.current().isnumeric() and not self.current() == "-":
            return NOT_PARSED

        start = self.pos
        if self.current_is_one_of("-"):
            self.inc()

        if self.current() == "0":
            self.inc()
        else:
            self.get_digits()

        if self.current_is_one_of("."):
            self.get_digits()

        if self.current_is_one_of("eE"):
            self.current_is_one_of("+-")
            if not self.get_digits():
                raise Exception()

        result = float(self.s[start: self.pos])
        if result % 1 == 0:
            result = int(result)

        self.consume_whitespace()

        return result

    def _parse_keyword(self, keyword, value):
        self.consume_whitespace()
        if self.s[self.pos: self.pos + len(keyword)] == keyword:
            self.pos += len(keyword)
            self.consume_whitespace()
            return value
        return NOT_PARSED

    def parse_true(self):
        return self._parse_keyword("true", True)

    def parse_false(self):
        return self._parse_keyword("false", False)

    def parse_null(self):
        return self._parse_keyword("null", None)

    def parse_string(self):
        self.consume_whitespace()

        if not self.current() == '"':
            return NOT_PARSED

        if not self.inc():
            raise e.UnmatchedDoubleQuoteException()

        result = []
        while self.current() != '"':
            if 0 <= ord(self.current()) <= 31:
                raise Exception("cannot have control char in string")

            if self.current() != "\\":
                result.append(self.current())

            else:
                if not self.inc():
                    raise e.UnmatchedDoubleQuoteException()

                match self.current():
                    case '"':
                        result.append('"')
                    case "\\":
                        result.append("\\")
                    case "/":
                        result.append("/")
                    case "b":
                        result.append("\b")
                    case "f":
                        result.append("\f")
                    case "n":
                        result.append("\n")
                    case "r":
                        result.append("\r")
                    case "t":
                        result.append("\t")
                    case "u":
                        if not self.inc():
                            raise e.UnmatchedDoubleQuoteException()
                        result.append(self.get_unicode())
                    case _:
                        raise Exception()

            if not self.inc():
                raise e.UnmatchedDoubleQuoteException()

        result = "".join(result)
        self.inc()
        return result

    def parse_array(self):
        self.consume_whitespace()
        if self.current() != "[":
            return NOT_PARSED

        self.depth += 1
        if self.depth > self.max_depth:
            raise e.MaxDepthExceededException()

        self.consume_whitespace()
        if not self.inc():
            raise e.UnmatchedBracketException()

        result = []
        trailing_comma = False
        while True:
            self.consume_whitespace()
            if self.pos == len(self.s):
                raise e.UnmatchedBracketException()

            if self.current() == "]":
                break

            value = self.parse_value()
            if value is NOT_PARSED:
                raise Exception()
            else:
                result.append(value)
                trailing_comma = False

            self.consume_whitespace()
            if self.current() == ",":
                trailing_comma = True
                if not self.inc():
                    raise e.UnmatchedBracketException()

        if trailing_comma:
            raise e.TrailingCommaException()

        self.inc()
        self.depth -= 1
        return result

    def parse_object(self):
        self.consume_whitespace()

        if self.current() != "{":
            return NOT_PARSED

        self.depth += 1
        if self.depth > self.max_depth:
            raise e.MaxDepthExceededException()

        if not self.inc():
            raise e.UnmatchedBraceException()

        result = {}
        trailing_comma = False
        while True:
            self.consume_whitespace()
            if self.pos == len(self.s):
                raise e.UnmatchedBraceException()

            if self.current() == "}":
                break

            key = self.parse_string()

            if key is NOT_PARSED:
                raise e.InvalidKeyException()

            if key in result:
                raise e.DuplicateKeyException()

            self.consume_whitespace()
            if self.current() != ":":
                raise e.ExpectedColonException()

            if not self.inc():
                raise e.MissingValueException()

            self.consume_whitespace()
            value = self.parse_value()

            if value is NOT_PARSED:
                raise Exception()

            result[key] = value
            trailing_comma = False

            self.consume_whitespace()
            if self.current() == ",":
                trailing_comma = True
                if not self.inc():
                    raise Exception("No }")

        if trailing_comma:
            raise e.TrailingCommaException()

        self.inc()
        self.depth -= 1
        return result

    def parse_value(self):
        result = self.parse_object()

        if result is NOT_PARSED:
            result = self.parse_array()

        if result is NOT_PARSED:
            result = self.parse_number()

        if result is NOT_PARSED:
            result = self.parse_string()

        if result is NOT_PARSED:
            result = self.parse_true()

        if result is NOT_PARSED:
            result = self.parse_false()

        if result is NOT_PARSED:
            result = self.parse_null()

        if result is NOT_PARSED:
            raise Exception()

        return result

    def parse(self, s):
        self.s = s
        self.pos = 0
        self.depth = 0
        self.consume_whitespace()
        if not self.current() in "{[":
            raise Exception()

        result = self.parse_value()

        self.consume_whitespace()
        if self.pos != len(self.s):
            raise Exception()

        return result
