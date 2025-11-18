import argparse
import base64
import inspect
import logging
import sys
from typing import Any, Callable, Dict, List, Union, get_args, get_origin

from fake import FAKER, PROVIDER_REGISTRY
from fastmcp import FastMCP

__title__ = "fake-py-mcp"
__version__ = "0.1"
__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2025 Artur Barseghyan"
__license__ = "MIT"
__all__ = (
    "MCP",
    "get_return_type",
    "serialise_result",
    "is_supported_type",
    "get_supported_params",
    "register_fakepy_tools",
    "server_info",
    "main",
)
# ----------------------------------------------------------------------------
# Logging setup
# ----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# MCP Server instance
# ----------------------------------------------------------------------------
MCP = FastMCP("fake.py MCP Server")

# ----------------------------------------------------------------------------
# Helper: Type mapping for fake.py methods
# ----------------------------------------------------------------------------
PROVIDER_LIST = sorted(PROVIDER_REGISTRY["fake.Faker"])


def get_return_type(method: Callable) -> Any:
    """Infer return type for MCP schema from method docstring or name."""
    name = method.__name__
    if name in {
        "bmp", "docx", "eml", "epub", "gif", "jpg", "odt", "pdf", "png", "ppm",
        "rtf", "svg", "tar", "tif", "wav", "zip"
    }:
        return str  # base64-encoded
    if name.endswith("_file"):
        return str  # file path
    if name in {"latitude_longitude"}:
        return List[float]
    if name in {
        "first_names",
        "last_names",
        "names",
        "usernames",
        "paragraphs",
        "sentences",
        "slugs",
        "texts",
        "words",
    }:
        return List[str]
    if name in {"uuid"}:
        return str
    if name in {"date"}:
        return str
    if name in {"date_time"}:
        return str
    if name in {"latitude", "longitude"}:
        return float
    if name in {"pybool"}:
        return bool
    if name in {"pyint", "year"}:
        return int
    return str


def serialise_result(name: str, result: Any) -> Any:
    """Serialise result for MCP transport."""
    if name in {
        "bmp",
        "docx",
        "eml",
        "epub",
        "gif",
        "jpg",
        "odt",
        "pdf",
        "png",
        "ppm",
        "rtf",
        "svg",
        "tar",
        "tif",
        "wav",
        "zip",
    }:
        if isinstance(result, bytes):
            return base64.b64encode(result).decode("ascii")
        return result
    if name == "uuid":
        return str(result)
    if name == "date":
        return (
            result.isoformat() if hasattr(result, "isoformat") else str(result)
        )
    if name == "date_time":
        return (
            result.isoformat() if hasattr(result, "isoformat") else str(result)
        )
    if name == "latitude_longitude":
        return list(result)
    return result

# ----------------------------------------------------------------------------
# Parameter support helpers
# ----------------------------------------------------------------------------

_SIMPLE_TYPES = {int, str, float, bool}


def is_supported_type(typ):
    """Return True if typ is a supported simple type or Optional thereof."""
    origin = get_origin(typ)
    if origin is Union:
        args = get_args(typ)
        # Only support Optional[T] where T is a simple type
        if len(args) == 2 and type(None) in args:
            other = args[0] if args[1] is type(None) else args[1]
            return other in _SIMPLE_TYPES
        return False
    return typ in _SIMPLE_TYPES


def get_supported_params(sig):
    """Return a list of (name, param) for supported parameters."""
    supported = []
    for name, param in sig.parameters.items():
        # Exclude *args, **kwargs, and any named 'options'
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue
        if name.lower() in {"options"}:
            continue
        if param.annotation is inspect.Parameter.empty:
            continue  # skip untyped
        if not is_supported_type(param.annotation):
            continue
        supported.append((name, param))
    return supported


# ----------------------------------------------------------------------------
# Dynamic tool registration (closure-safe)
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Dynamic tool registration (closure-safe)
# ----------------------------------------------------------------------------

def _create_tool_wrapper(method, attr, return_type, doc, params, annotations):
    """Factory to create a tool function with arguments."""

    # Build the function with the correct signature using closure
    def tool_fn(*args, **kwargs):
        # Map args to parameter names
        call_kwargs = {}
        for i, (name, param) in enumerate(params):
            if name in kwargs:
                call_kwargs[name] = kwargs[name]
            elif i < len(args):
                call_kwargs[name] = args[i]
            elif param.default is not inspect.Parameter.empty:
                call_kwargs[name] = param.default
            else:
                raise TypeError(f"Missing required argument: {name}")
        try:
            result = method(**call_kwargs)
            return serialise_result(attr, result)
        except Exception as err:
            LOGGER.error(f"Error in {attr}(): {err}")
            raise RuntimeError(f"fake.py error in {attr}(): {err}") from err

    # Set function metadata
    tool_fn.__name__ = attr
    tool_fn.__doc__ = doc
    tool_fn.__annotations__ = {
        **annotations,
        "return": return_type,
    }
    # Set signature to match the original method
    tool_fn.__signature__ = inspect.Signature(
        parameters=[param for _, param in params],
        return_annotation=return_type
    )
    return tool_fn


def _create_simple_wrapper(method, attr, return_type, doc):
    """Factory to create a tool function without arguments."""

    def tool_fn():
        try:
            result = method()
            return serialise_result(attr, result)
        except Exception as err:
            LOGGER.error(f"Error in {attr}(): {err}")
            raise RuntimeError(f"fake.py error in {attr}(): {err}") from err

    tool_fn.__name__ = attr
    tool_fn.__doc__ = doc
    tool_fn.__annotations__ = {"return": return_type}
    return tool_fn


def register_fakepy_tools():
    """Dynamically register all FAKER methods as MCP tools with arg support."""
    for attr in PROVIDER_LIST:
        if attr.startswith("_"):
            continue
        method = getattr(FAKER, attr)
        if not callable(method):
            continue
        if hasattr(MCP, attr):
            continue

        sig = inspect.signature(method)
        params = get_supported_params(sig)
        return_type = get_return_type(method)
        doc = inspect.getdoc(method) or f"Fake.py: {attr}()"

        if params:
            annotations = {name: param.annotation for name, param in params}
            # Pass explicit arguments to the helper
            tool_fn = _create_tool_wrapper(
                method, attr, return_type, doc, params, annotations
            )
            MCP.tool(name=attr, description=doc)(tool_fn)
        else:
            # Pass explicit arguments to the helper
            tool_fn = _create_simple_wrapper(method, attr, return_type, doc)
            MCP.tool(name=attr, description=doc)(tool_fn)


register_fakepy_tools()

# ----------------------------------------------------------------------------
# Example: Server info tool
# ----------------------------------------------------------------------------


@MCP.tool()
def server_info() -> Dict[str, Any]:
    """
    Get information about this MCP server and available fake.py tools.
    """
    return {
        "server": "fake.py MCP Server",
        "tools": sorted([
            attr for attr in PROVIDER_LIST
            if not attr.startswith("_") and callable(getattr(FAKER, attr))

        ]),
        "docs": "https://github.com/barseghyanartur/fake.py"
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="fake.py MCP Server — run in stdio or http mode."
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["stdio", "http", "sse"],
        default="stdio",
        help="Transport mode: 'stdio' (default) or 'http'",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for HTTP mode (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8005,
        help="Port for HTTP mode (default: 8005)",
    )
    args = parser.parse_args()

    if args.mode == "http":
        LOGGER.info(
            f"Starting MCP server in HTTP mode on {args.host}:{args.port}"
        )
        MCP.run(transport="http", host=args.host, port=args.port)
    elif args.mode == "sse":
        LOGGER.info(
            f"Starting MCP server in SSE mode on {args.host}:{args.port}"
        )
        MCP.run(transport="sse", host=args.host, port=args.port)
    else:
        LOGGER.info("Starting MCP server in STDIO mode")
        MCP.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        LOGGER.info("Server stopped by user")
        sys.exit(0)
