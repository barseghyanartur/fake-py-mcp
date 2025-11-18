import datetime
import inspect
import sys
from typing import List, Optional, Union
from unittest.mock import MagicMock, patch

import pytest
from fakepy_mcp import (
    get_return_type,
    get_supported_params,
    is_supported_type,
    main,
    serialise_result,
)

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2025 Artur Barseghyan"
__license__ = "MIT"
__all__ = (
    "make_method",
    "test_get_return_type",
    "test_serialise_result_base64",
    "test_serialise_result_uuid",
    "test_serialise_result_date",
    "test_serialise_result_date_time",
    "test_serialise_result_latitude_longitude",
    "test_serialise_result_passthrough",
    "test_is_supported_type",
    "test_get_supported_params_filters",
    "test_get_supported_params_options",
    "test_main_stdio",
    "test_main_http",
    "test_main_sse",
)

# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Test helpers
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------

# ----------------------------------------------------------------------------
# get_return_type tests
# ----------------------------------------------------------------------------

def make_method(name):
    def fn(): pass
    fn.__name__ = name
    return fn


@pytest.mark.parametrize("name,expected", [
    ("bmp", str),
    ("pdf", str),
    ("png_file", str),
    ("latitude_longitude", List[float]),
    ("first_names", List[str]),
    ("uuid", str),
    ("date", str),
    ("date_time", str),
    ("latitude", float),
    ("longitude", float),
    ("pybool", bool),
    ("pyint", int),
    ("year", int),
    ("random", str),
])
def test_get_return_type(name, expected):
    method = make_method(name)
    assert get_return_type(method) == expected

# ----------------------------------------------------------------------------
# serialise_result tests
# ----------------------------------------------------------------------------


def test_serialise_result_base64():
    data = b"hello"
    result = serialise_result("bmp", data)
    import base64
    assert result == base64.b64encode(data).decode("ascii")


def test_serialise_result_uuid():
    import uuid
    u = uuid.uuid4()
    assert serialise_result("uuid", u) == str(u)


def test_serialise_result_date():
    d = datetime.date(2024, 1, 2)
    assert serialise_result("date", d) == "2024-01-02"


def test_serialise_result_date_time():
    dt = datetime.datetime(
        2024, 1, 2, 3, 4, 5
    )
    assert serialise_result("date_time", dt) == "2024-01-02T03:04:05"


def test_serialise_result_latitude_longitude():
    assert serialise_result(
        "latitude_longitude", (1.1, 2.2)
    ) == [1.1, 2.2]


def test_serialise_result_passthrough():
    assert serialise_result("random", 123) == 123

# ----------------------------------------------------------------------------
# is_supported_type tests
# ----------------------------------------------------------------------------


@pytest.mark.parametrize("typ,expected", [
    (int, True),
    (str, True),
    (float, True),
    (bool, True),
    (Optional[int], True),
    (Optional[str], True),
    (Union[int, None], True),
    (Union[str, None], True),
    (Union[int, str], False),
    (list, False),
    (dict, False),
])
def test_is_supported_type(typ, expected):
    assert is_supported_type(typ) == expected

# ----------------------------------------------------------------------------
# get_supported_params tests
# ----------------------------------------------------------------------------

def test_get_supported_params_filters():
    def fn(a: int, b: str, c, *args, **kwargs): pass
    sig = inspect.signature(fn)
    params = get_supported_params(sig)
    assert ("a", sig.parameters["a"]) in params
    assert ("b", sig.parameters["b"]) in params
    assert all(name != "c" for name, _ in params)  # c is untyped
    assert all(name != "args" for name, _ in params)
    assert all(name != "kwargs" for name, _ in params)


def test_get_supported_params_options():
    def fn(options: int, foo: int): pass
    sig = inspect.signature(fn)
    params = get_supported_params(sig)
    assert ("foo", sig.parameters["foo"]) in params
    assert all(name != "options" for name, _ in params)

# ----------------------------------------------------------------------------
# Test dynamic tool registration
# ----------------------------------------------------------------------------
# TODO: Add tests

# ----------------------------------------------------------------------------
# Test server info
# ----------------------------------------------------------------------------
# TODO: Add tests

# ----------------------------------------------------------------------------
# Test main function
# ----------------------------------------------------------------------------


def test_main_stdio(monkeypatch):
    fake_run = MagicMock()
    monkeypatch.setattr("fakepy_mcp.MCP.run", fake_run)
    test_args = ["prog"]
    with patch.object(sys, "argv", test_args):
        main()
    fake_run.assert_called_once_with()


def test_main_http(monkeypatch):
    fake_run = MagicMock()
    monkeypatch.setattr("fakepy_mcp.MCP.run", fake_run)
    test_args = ["prog", "http", "--host", "127.0.0.1", "--port", "1234"]
    with patch.object(sys, "argv", test_args):
        main()
    fake_run.assert_called_once_with(
        transport="http", host="127.0.0.1", port=1234
    )


def test_main_sse(monkeypatch):
    fake_run = MagicMock()
    monkeypatch.setattr("fakepy_mcp.MCP.run", fake_run)
    test_args = ["prog", "sse"]
    with patch.object(sys, "argv", test_args):
        main()
    fake_run.assert_called_once_with(
        transport="sse", host="0.0.0.0", port=8005
    )
