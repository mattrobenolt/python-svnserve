class literal(str):
    """A unique type to distinguish between str and a literal"""
    pass


class MarshallError(Exception):
    """A Marshall error."""


class NeedMoreData(MarshallError):
    """More data needed."""


def encode(data):
    """Marshall a Python data item.

    :param x: Data item
    :return: encoded string
    """
    if isinstance(data, int):
        return "%d " % data
    elif isinstance(data, (list, tuple)):
        return "( " + "".join(map(encode, data)) + ") "
    elif isinstance(data, literal):
        return "%s " % data
    elif isinstance(data, str):
        return "%d:%s " % (len(data), data)
    elif isinstance(data, unicode):
        return "%d:%s " % (len(data), data.encode("utf-8"))
    elif isinstance(data, bool):
        if data:
            return "true "
        else:
            return "false "
    raise ValueError("Unable to marshall type %s" % repr(data))


def decode(x):
    """Unmarshall the next item from a text.

    :param x: Text to parse
    :return: tuple with unpacked item and remaining text
    """
    whitespace = ['\n', ' ']
    if len(x) == 0:
        raise NeedMoreData("Not enough data")
    if x[0] == "(":  # list follows
        if len(x) <= 1:
            raise NeedMoreData("Missing whitespace")
        if x[1] != " ":
            raise MarshallError("missing whitespace after list start")
        x = x[2:]
        ret = []
        try:
            while x[0] != ")":
                (x, n) = decode(x)
                ret.append(n)
        except IndexError:
            raise NeedMoreData("List not terminated")

        if len(x) <= 1:
            raise NeedMoreData("Missing whitespace")

        if not x[1] in whitespace:
            raise MarshallError("Expected space, got %c" % x[1])

        return (x[2:], ret)
    elif x[0].isdigit():
        num = ""
        # Check if this is a string or a number
        while x[0].isdigit():
            num += x[0]
            x = x[1:]
        num = int(num)

        if x[0] in whitespace:
            return (x[1:], num)
        elif x[0] == ":":
            if len(x) < num:
                raise NeedMoreData("Expected string of length %r" % num)
            return (x[num + 2:], x[1:num + 1])
        else:
            raise MarshallError("Expected whitespace or ':', got '%c" % x[0])
    elif x[0].isalpha():
        ret = ""
        # Parse literal
        try:
            while x[0].isalpha() or x[0].isdigit() or x[0] == '-':
                ret += x[0]
                x = x[1:]
        except IndexError:
            raise NeedMoreData("Expected literal")

        if not x[0] in whitespace:
            raise MarshallError("Expected whitespace, got %c" % x[0])

        return (x[1:], ret)
    else:
        raise MarshallError("Unexpected character '%c'" % x[0])

