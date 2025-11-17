import json
import subprocess
import sys
import time
from typing import Any, Dict, List
import pytest
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------
HOST = "127.0.0.1"
PORT = 8005
BASE_URL = f"http://{HOST}:{PORT}"
SERVER_STARTUP_TIMEOUT = 5  # seconds
SERVER_URL = "http://127.0.0.1:8005"

# ----------------------------------------------------------------------------
# Helper: HTTP session with retry
# ----------------------------------------------------------------------------
def get_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    return session

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------
@pytest.fixture(scope="module")
def http_server():
    """Start the server in HTTP mode."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "fakepy_mcp.py",
            "http",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=1)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.2)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start in HTTP mode")

    yield proc

    proc.terminate()
    proc.wait(timeout=3)


@pytest.fixture(scope="module")
def sse_server():
    """Start the server in SSE mode."""
    proc = subprocess.Popen(
        [
            sys.executable,
            "fakepy_mcp.py",
            "sse",
            "--host",
            HOST,
            "--port",
            str(PORT),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    # Wait for server to start
    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            resp = requests.get(f"{BASE_URL}/health", timeout=1)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            time.sleep(0.2)
    else:
        proc.terminate()
        raise RuntimeError("Server failed to start in SSE mode")

    yield proc

    proc.terminate()
    proc.wait(timeout=3)


# ----------------------------------------------------------------------------
# HTTP/SSE Mode Tests
# ----------------------------------------------------------------------------
def test_server_info_http(http_server):
    """Test server_info returns correct structure and tool list."""
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={"tool": "server_info"},
        timeout=5,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["server"] == "fake.py MCP Server"
    assert isinstance(data["tools"], list)
    assert len(data["tools"]) > 50  # fake.py has many providers
    assert "name" in data["tools"]
    assert "email" in data["tools"]
    assert "uuid" in data["tools"]
    assert data["docs"] == "https://github.com/barseghyanartur/fake.py"


def test_server_info_sse(sse_server):
    """Same as above but in SSE mode."""
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={"tool": "server_info"},
        timeout=5,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["server"] == "fake.py MCP Server"
    assert isinstance(data["tools"], list)
    assert "name" in data["tools"]
    assert "email" in data["tools"]


@pytest.mark.parametrize("tool_name", [
    "name", "email", "uuid", "pyint", "pybool", "date", "date_time"
])
def test_basic_tools_return_correct_types_http(http_server, tool_name):
    """Test basic tools return expected types."""
    session = get_session()
    payload = {"tool": tool_name}
    response = session.post(f"{BASE_URL}/invoke", json=payload, timeout=5)
    assert response.status_code == 200
    result = response.json()

    expected_types = {
        "name": str,
        "email": str,
        "uuid": str,
        "pyint": int,
        "pybool": bool,
        "date": str,
        "date_time": str,
    }

    assert isinstance(result, expected_types[tool_name])


def test_latitude_longitude_returns_list_of_floats(http_server):
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={"tool": "latitude_longitude"},
        timeout=5,
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(x, float) for x in result)


def test_binary_file_returns_base64_string(http_server):
    binary_tools = ["png", "jpg", "pdf", "gif"]
    session = get_session()

    for tool in binary_tools:
        response = session.post(
            f"{BASE_URL}/invoke",
            json={"tool": tool},
            timeout=5,
        )
        assert response.status_code == 200
        result = response.json()
        assert isinstance(result, str)
        # Should be valid base64
        try:
            import base64
            base64.b64decode(result)
        except Exception as e:
            pytest.fail(f"Invalid base64 for {tool}: {e}")


def test_parameterized_tool_with_valid_args(http_server):
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={
            "tool": "pyint",
            "args": {"min_value": 10, "max_value": 20}
        },
        timeout=5,
    )
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, int)
    assert 10 <= result <= 20


def test_parameterized_tool_missing_required_arg(http_server):
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={
            "tool": "pyint",
            "args": {"min_value": 10}  # missing max_value
        },
        timeout=5,
    )
    assert response.status_code == 400  # FastMCP returns 400 on error
    data = response.json()
    assert "error" in data
    assert "missing" in data["error"].lower() or "required" in data["error"].lower()


def test_unknown_tool_returns_error(http_server):
    session = get_session()
    response = session.post(
        f"{BASE_URL}/invoke",
        json={"tool": "this_tool_does_not_exist"},
        timeout=5,
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data


def test_tool_list_endpoint(http_server):
    """Test /tools endpoint exists and returns list."""
    session = get_session()
    response = session.get(f"{BASE_URL}/tools", timeout=5)
    assert response.status_code == 200
    tools = response.json()
    assert isinstance(tools, list)
    assert "server_info" in tools
    assert "name" in tools
    assert "uuid" in tools


def test_health_endpoint(http_server):
    session = get_session()
    response = session.get(f"{BASE_URL}/health", timeout=5)
    assert response.status_code == 200
    assert response.text == "OK"


# ----------------------------------------------------------------------------
# STDIO Mode Test (via subprocess)
# ----------------------------------------------------------------------------
def test_stdio_mode_invocation():
    """Test server in stdio mode via subprocess."""
    proc = subprocess.Popen(
        [sys.executable, "fakepy_mcp.py", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Send list_tools request
    list_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "list_tools",
        "params": {}
    }
    proc.stdin.write(json.dumps(list_request) + "\n")
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline().strip()
    response = json.loads(response_line)

    assert response["id"] == 1
    assert "result" in response
    tools = response["result"]
    assert isinstance(tools, list)
    assert "server_info" in tools
    assert "name" in tools

    # Test invoke server_info
    invoke_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "invoke",
        "params": {"tool": "server_info"}
    }
    proc.stdin.write(json.dumps(invoke_request) + "\n")
    proc.stdin.flush()

    response_line = proc.stdout.readline().strip()
    response = json.loads(response_line)

    assert response["id"] == 2
    result = response["result"]
    assert result["server"] == "fake.py MCP Server"
    assert "tools" in result
    assert isinstance(result["tools"], list)

    proc.stdin.close()
    proc.terminate()
    proc.wait(timeout=3)


# ----------------------------------------------------------------------------
# Registration & Type Inference Tests (unit-style, no server needed)
# ----------------------------------------------------------------------------
def test_get_return_type_inference():
    from fakepy_mcp import get_return_type
    from fake import FAKER

    assert get_return_type(FAKER.name) == str
    assert get_return_type(FAKER.uuid) == str
    assert get_return_type(FAKER.pyint) == int
    assert get_return_type(FAKER.pybool) == bool
    assert get_return_type(FAKER.latitude_longitude) == List[float]
    assert get_return_type(FAKER.png) == str  # base64
    assert get_return_type(FAKER.pdf) == str  # base64


def test_serialise_result_handles_binary():
    from fakepy_mcp import serialise_result
    import base64

    dummy_bytes = b"fake-image-data"
    result = serialise_result("png", dummy_bytes)
    assert isinstance(result, str)
    assert base64.b64decode(result) == dummy_bytes

    result = serialise_result("name", "John Doe")
    assert result == "John Doe"


def test_is_supported_type():
    from fakepy_mcp import is_supported_type
    from typing import Optional

    assert is_supported_type(int) is True
    assert is_supported_type(str) is True
    assert is_supported_type(float) is True
    assert is_supported_type(bool) is True
    assert is_supported_type(Optional[int]) is True
    assert is_supported_type(Optional[str]) is True

    assert is_supported_type(list) is False
    assert is_supported_type(dict) is False
    assert is_supported_type(Optional[list]) is False


def test_get_supported_params_filters_correctly():
    from fakepy_mcp import get_supported_params
    import inspect

    def sample(a: int, b: str, c: float = 1.0, *, d: bool, **kwargs):
        pass

    sig = inspect.signature(sample)
    supported = get_supported_params(sig)

    names = [name for name, _ in supported]
    assert "a" in names
    assert "b" in names
    assert "c" in names
    assert "d" in names
    assert "kwargs" not in names


def test_register_fakepy_tools_does_not_raise():
    # Re-import to avoid side effects
    import importlib
    import fakepy_mcp
    importlib.reload(fakepy_mcp)

    # Should not raise
    assert "name" in dir(fakepy_mcp.MCP)
    assert "server_info" in dir(fakepy_mcp.MCP)
