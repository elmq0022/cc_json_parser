class BaseException(Exception): ...


class UnmatchedDoubleQuoteException(BaseException): ...


class UnmatchedBracketException(BaseException): ...


class TrailingCommaException(BaseException): ...


class UnmatchedBraceException(BaseException): ...


class InvalidKeyException(BaseException): ...


class DuplicateKeyException(BaseException): ...


class ExpectedColonException(BaseException): ...


class MissingValueException(BaseException): ...