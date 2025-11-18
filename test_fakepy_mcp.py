import datetime
import inspect
import sys
from typing import List, Optional, Union
from unittest.mock import MagicMock, patch

import pytest
from fakepy_mcp import (
    MCP,
    get_return_type,
    get_supported_params,
    is_supported_type,
    main,
    serialise_result,
)
from fastmcp.client import Client
from inline_snapshot import snapshot

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


# ----------------------------------------------------------------------------
# Pattern: Golden Master / Snapshot Testing
# We use inline-snapshot to freeze the expected state of the tool registry.
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_registry_snapshot():
    """
    Pattern: Golden Master (API Surface)

    This test fetches the list of all registered tools and compares them
    against a stored snapshot in this file.

    If you 'fake.py' providers are updated or filtering logic changed
    (get_supported_params), this test will fail.

    Fix is easy - accept the changes by running:

        pytest --inline-snapshot=fix,create
    """
    async with Client(MCP) as client:
        tools = await client.list_tools()
        # We sort the tools to ensure deterministic snapshotting
        tool_names = sorted([t.name for t in tools])

        # When you first run this, it will fail.
        # Run `pytest --inline-snapshot=create` to populate the list below.
        assert tool_names == snapshot(
            [
                "bin","bin_file","bmp","bmp_file","city","company_email",
                "country","country_code","date","date_time","dir_path",
                "docx","docx_file","domain_name","email","eml","eml_file",
                "epub","epub_file","file_extension","file_name","file_path",
                "first_name","first_names","free_email","free_email_domain",
                "generic_file","geo_location","gif","gif_file","iban",
                "image","image_url","ipv4","isbn10","isbn13","jpg",
                "jpg_file","last_name","last_names","latitude",
                "latitude_longitude","lazy_string_template","locale",
                "longitude","mime_type","names","odt","odt_file",
                "paragraph","paragraphs","password","pdf","pdf_file",
                "png","png_file","ppm","ppm_file","pybool","pydecimal",
                "pyfloat","pyint","pystr","random_choice","random_sample",
                "randomise_string","rtf","rtf_file","sentence","sentences",
                "server_info","slug","slugs","string_template","svg",
                "svg_file","tar","tar_file","text","text_pdf",
                "text_pdf_file","texts","tif","tif_file","time","tld",
                "txt_file","url","username","usernames","uuid","uuids",
                "wav","wav_file","word","words","year","zip","zip_file",
            ]
        )


@pytest.mark.asyncio
async def test_tool_schema_snapshot():
    """
    Pattern: Schema Validation Snapshot

    Verifies the input schema of a complex tool to ensure types are
    mapped correctly (e.g., int -> integer, str -> string).
    """
    async with Client(MCP) as client:
        tools = await client.list_tools()
        # We pick a specific tool that has arguments, e.g., 'password' or
        # 'sentence'.
        # Adjust 'sentence' to a tool you know exists in your version of
        # fake.py.
        target_tool = next((t for t in tools if t.name == "sentence"), None)

        if target_tool:
            # We snapshot the JSON schema of the arguments.
            # This ensures we don't accidentally break argument parsing.
            assert target_tool.inputSchema == snapshot(
                {
                    "properties":{
                        "nb_words":{"default":5 ,"type":"integer"},
                        "suffix":{"default":".","type":"string"}
                    },
                    "type":"object",
                }
            )

# ----------------------------------------------------------------------------
# CLI / Entrypoint Tests
# ----------------------------------------------------------------------------

def test_main_modes(monkeypatch):
    """
    Verify CLI argument parsing.
    Rationale: Ensures the server starts in the correct mode based on flags.
    """
    fake_run = MagicMock()
    monkeypatch.setattr("fakepy_mcp.MCP.run", fake_run)

    # Test HTTP
    with patch.object(sys, "argv", ["prog", "http", "--port", "9000"]):
        main()
    fake_run.assert_called_with(transport="http", host="0.0.0.0", port=9000)

    # Test STDIO (Default)
    with patch.object(sys, "argv", ["prog"]):
        main()
    fake_run.assert_called_with()


@pytest.mark.asyncio
async def test_custom_server_info_tool():
    """
    Pattern: Custom Tool Logic
    Verifies the manually defined 'server_info' tool works alongside
    dynamic tools.
    """
    async with Client(MCP) as client:
        result = await client.call_tool("server_info")
        data = result.content[0].text

        # Depending on how your `server_info` returns data (dict vs json
        # string), FastMCP tools usually return text. If your tool returns a
        # Dict, FastMCP serializes it to JSON text automatically.
        import json
        parsed = json.loads(data)

        assert parsed["server"] == "fake.py MCP Server"
        assert "tools" in parsed
        assert isinstance(parsed["tools"], list)
