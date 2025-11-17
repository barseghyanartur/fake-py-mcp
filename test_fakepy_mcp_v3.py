import sys
import base64
import uuid
import datetime
import inspect
import json
import subprocess
from typing import Optional, Union, List

import pytest

# Import the actual module under test
import fakepy_mcp

# --- 1. Helper Function Tests ---

def test_get_return_type_with_real_methods():
    # Use real FAKER methods or dummy functions with specific names
    class Dummy:
        def bmp(self): pass
        def latitude_longitude(self): pass
        def first_names(self): pass
        def uuid(self): pass
        def date(self): pass
        def date_time(self): pass
        def latitude(self): pass
        def pybool(self): pass
        def pyint(self): pass
        def year(self): pass
        def random(self): pass

    d = Dummy()
    assert fakepy_mcp.get_return_type(d.bmp) == str
    assert fakepy_mcp.get_return_type(d.latitude_longitude) == List[float]
    assert fakepy_mcp.get_return_type(d.first_names) == List[str]
    assert fakepy_mcp.get_return_type(d.uuid) == str
    assert fakepy_mcp.get_return_type(d.date) == str
    assert fakepy_mcp.get_return_type(d.date_time) == str
    assert fakepy_mcp.get_return_type(d.latitude) == float
    assert fakepy_mcp.get_return_type(d.pybool) == bool
    assert fakepy_mcp.get_return_type(d.pyint) == int
    assert fakepy_mcp.get_return_type(d.year) == int
    assert fakepy_mcp.get_return_type(d.random) == str

def test_serialise_result_various_types():
    # bytes to base64
    data = b"hello"
    result = fakepy_mcp.serialise_result("bmp", data)
    assert result == base64.b64encode(data).decode("ascii")
    # uuid to str
    u = uuid.uuid4()
    assert fakepy_mcp.serialise_result("uuid", u) == str(u)
    # date to isoformat
    d = datetime.date(2024, 1, 2)
    assert fakepy_mcp.serialise_result("date", d) == "2024-01-02"
    # datetime to isoformat
    dt = datetime.datetime(2024, 1, 2, 3, 4, 5)
    assert fakepy_mcp.serialise_result("date_time", dt) == "2024-01-02T03:04:05"
    # latitude_longitude to list
    assert fakepy_mcp.serialise_result("latitude_longitude", (1.1, 2.2)) == [1.1, 2.2]
    # passthrough
    assert fakepy_mcp.serialise_result("random", 123) == 123

def test_is_supported_type_various():
    assert fakepy_mcp.is_supported_type(int)
    assert fakepy_mcp.is_supported_type(str)
    assert fakepy_mcp.is_supported_type(float)
    assert fakepy_mcp.is_supported_type(bool)
    assert fakepy_mcp.is_supported_type(Optional[int])
    assert fakepy_mcp.is_supported_type(Union[int, None])
    assert not fakepy_mcp.is_supported_type(list)
    assert not fakepy_mcp.is_supported_type(dict)
    assert not fakepy_mcp.is_supported_type(Union[int, str])

def test_get_supported_params_filters():
    def fn(a: int, b: str, c, *args, **kwargs): pass
    sig = inspect.signature(fn)
    params = fakepy_mcp.get_supported_params(sig)
    names = [name for name, _ in params]
    assert "a" in names
    assert "b" in names
    assert "c" not in names
    assert "args" not in names
    assert "kwargs" not in names

def test_get_supported_params_options():
    def fn(options: int, foo: int): pass
    sig = inspect.signature(fn)
    params = fakepy_mcp.get_supported_params(sig)
    names = [name for name, _ in params]
    assert "foo" in names
    assert "options" not in names

# --- 2. Dynamic Tool Registration Integration Tests ---

def test_register_fakepy_tools_and_tool_invocation():
    # Re-register tools to ensure a clean state
    fakepy_mcp.register_fakepy_tools()
    # Check that some known tools are registered
    for tool_name in ["name", "email", "address"]:
        assert hasattr(fakepy_mcp.MCP, tool_name)
        tool_fn = getattr(fakepy_mcp.MCP, tool_name)
        # Should be callable and return a string
        result = tool_fn()
        assert isinstance(result, str)
        # Check signature and annotations
        sig = inspect.signature(tool_fn)
        assert sig.return_annotation == str

def test_dynamic_tool_signature_and_closure():
    # Find a tool with parameters (e.g., 'pyint' or similar)
    for tool_name in fakepy_mcp.PROVIDER_LIST:
        tool_fn = getattr(fakepy_mcp.MCP, tool_name, None)
        if tool_fn is not None:
            sig = inspect.signature(tool_fn)
            if sig.parameters:
                # Try calling with positional and keyword arguments
                args = []
                kwargs = {}
                for i, (param_name, param) in enumerate(sig.parameters.items()):
                    if param.default is inspect.Parameter.empty:
                        # Required param: use a simple value
                        if param.annotation == int:
                            args.append(42)
                        elif param.annotation == str:
                            args.append("foo")
                        elif param.annotation == float:
                            args.append(3.14)
                        elif param.annotation == bool:
                            args.append(True)
                        else:
                            args.append(None)
                    else:
                        # Optional param: skip
                        pass
                # Call with positional args
                result = tool_fn(*args)
                assert result is not None
                # Call with keyword args
                kw = {k: v for k, v in zip(sig.parameters.keys(), args)}
                result2 = tool_fn(**kw)
                assert result2 is not None
                break

def test_dynamic_tool_error_handling():
    # Find a tool with a required parameter and call it without arguments
    for tool_name in fakepy_mcp.PROVIDER_LIST:
        tool_fn = getattr(fakepy_mcp.MCP, tool_name, None)
        if tool_fn is not None:
            sig = inspect.signature(tool_fn)
            if sig.parameters:
                # Should raise TypeError if required argument is missing
                with pytest.raises(TypeError):
                    tool_fn()
                break

# --- 3. Server Info Tests ---

def test_server_info_structure_and_content():
    info = fakepy_mcp.server_info()
    assert isinstance(info, dict)
    assert "server" in info
    assert "tools" in info
    assert "docs" in info
    assert info["server"] == "fake.py MCP Server"
    assert isinstance(info["tools"], list)
    assert "https://" in info["docs"]
    # Check that at least one known tool is listed
    assert "name" in info["tools"]

# --- 4. CLI Argument Parsing and Main Functionality ---

def test_main_stdio_mode(tmp_path):
    # Run the script as a subprocess in stdio mode
    result = subprocess.run(
        [sys.executable, "fakepy_mcp.py", "stdio"],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    # Should start the server (will block or print startup message)
    assert result.returncode == 0 or result.returncode == 130  # 130 = KeyboardInterrupt
    assert "STDIO mode" in result.stdout or "STDIO mode" in result.stderr

def test_main_http_mode(tmp_path):
    # Run the script as a subprocess in http mode (should print startup message)
    result = subprocess.run(
        [sys.executable, "fakepy_mcp.py", "http", "--host", "127.0.0.1", "--port", "9001"],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0 or result.returncode == 130
    assert "HTTP mode" in result.stdout or "HTTP mode" in result.stderr

def test_main_sse_mode(tmp_path):
    # Run the script as a subprocess in sse mode (should print startup message)
    result = subprocess.run(
        [sys.executable, "fakepy_mcp.py", "sse"],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0 or result.returncode == 130
    assert "SSE mode" in result.stdout or "SSE mode" in result.stderr

def test_main_invalid_mode(tmp_path):
    # Should exit with error for invalid mode
    result = subprocess.run(
        [sys.executable, "fakepy_mcp.py", "invalidmode"],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode != 0
    assert "invalid choice" in result.stderr.lower()

def test_main_help(tmp_path):
    # Should print help and exit
    result = subprocess.run(
        [sys.executable, "fakepy_mcp.py", "--help"],
        capture_output=True,
        text=True,
        cwd=tmp_path
    )
    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()

# --- 5. JSON Serialization of server_info ---

def test_server_info_json_serialization():
    info = fakepy_mcp.server_info()
    s = json.dumps(info)
    info2 = json.loads(s)
    assert info2["server"] == info["server"]
    assert info2["tools"] == info["tools"]

