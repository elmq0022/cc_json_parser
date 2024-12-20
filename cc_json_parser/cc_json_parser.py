import string

from cc_json_parser import exceptions as e


class NotParsed:
    """
    The single global instance here is a guard value
    return by the specific parsing methods don't
    find anything specific to parse
    """

    ...


not_parsed = NotParsed()


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

    def current_is_one_of(self, chars: str, inc: bool = True):
        if self.current() in chars:
            if inc:
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
        last_was_numeric = 0
        got_digits = False

        if self.current().isnumeric():
            got_digits = True

        while self.current().isnumeric():
            if not self.inc():
                last_was_numeric = 1
                break

        return last_was_numeric, got_digits

    def parse_number(self):
        self.consume_whitespace()
        if not self.current().isnumeric() and not self.current() == "-":
            return not_parsed

        start = self.pos
        if self.current_is_one_of("-"):
            self.inc()

        if self.current_is_one_of("0", inc=False):
            if not self.inc():
                return 0

            if self.current().isnumeric():
                raise Exception()
            last_was_numeric = 0
        else:
            last_was_numeric, _ = self.get_digits()

        if self.current_is_one_of("."):
            last_was_numeric, _ = self.get_digits()

        if self.current_is_one_of("eE"):
            self.current_is_one_of("+-")
            last_was_numeric, got_digits = self.get_digits()
            if not got_digits:
                raise Exception()

        result = float(self.s[start: self.pos + last_was_numeric])
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
        return not_parsed

    def parse_true(self):
        return self._parse_keyword("true", True)

    def parse_false(self):
        return self._parse_keyword("false", False)

    def parse_null(self):
        return self._parse_keyword("null", None)

    def parse_string(self):
        self.consume_whitespace()

        if not self.current() == '"':
            return not_parsed

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
        self.inc()  # hmmm .... suspect
        self.consume_whitespace()
        # should I inc here as well
        return result

    def parse_array(self):
        self.consume_whitespace()
        if self.current() != "[":
            return not_parsed

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
            if value is not_parsed:
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
            return not_parsed

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

            if key is not_parsed:
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

            if value is not_parsed:
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

        if result is not_parsed:
            result = self.parse_array()

        if result is not_parsed:
            result = self.parse_number()

        if result is not_parsed:
            result = self.parse_string()

        if result is not_parsed:
            result = self.parse_true()

        if result is not_parsed:
            result = self.parse_false()

        if result is not_parsed:
            result = self.parse_null()

        if result is not_parsed:
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
