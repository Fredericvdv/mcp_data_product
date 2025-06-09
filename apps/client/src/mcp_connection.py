"""
MCP Server Connection Utilities

This module provides utilities for connecting to MCP servers with proper
resource management and error handling.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from apps.client.src.logging_config import logger


@asynccontextmanager
async def connect_to_mcp_server(
    server_script_path: str = "apps/mcp_server/src/server.py",
    command: str = "python",
    timeout: Optional[float] = 30.0,
) -> AsyncGenerator[ClientSession, None]:
    """
    Connect to an MCP server using stdio transport.

    This context manager handles the complete lifecycle of the MCP connection:
    - Sets up stdio transport parameters
    - Establishes connection with proper resource management
    - Initializes the session with timeout
    - Ensures cleanup on exit

    Args:
        server_script_path: Path to the MCP server script
        command: Command to run the server (default: "python")
        timeout: Connection timeout in seconds (default: 30.0)

    Yields:
        ClientSession: An initialized MCP client session

    Raises:
        asyncio.TimeoutError: If connection times out
        ConnectionError: If connection fails

    Example:
        async with connect_to_mcp_server() as session:
            tools = await session.list_tools()
            result = await session.call_tool("add", {"a": 1, "b": 2})
    """
    # Define server parameters
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
    )

    try:
        # Connect to the server with proper resource management and timeout
        async with asyncio.timeout(timeout) if timeout else asyncio.nullcontext():
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    try:
                        # Initialize the connection
                        await session.initialize()
                        logger.info(
                            f"Successfully connected to MCP server: {server_script_path}"
                        )

                        # Yield the initialized session
                        yield session

                    except Exception as e:
                        logger.error(f"Failed to initialize MCP session: {e}")
                        raise ConnectionError(
                            f"MCP session initialization failed: {e}"
                        ) from e
                    finally:
                        logger.debug("MCP session cleanup completed")

    except asyncio.TimeoutError:
        logger.error(f"Connection to MCP server timed out after {timeout}s")
        raise
    except Exception as e:
        logger.error(f"Failed to connect to MCP server: {e}")
        raise ConnectionError(f"MCP server connection failed: {e}") from e


async def get_server_info(session: ClientSession) -> Dict[str, Any]:
    """
    Get comprehensive information about the connected MCP server.

    Args:
        session: An active MCP client session

    Returns:
        Dict containing server tools, resources, and other metadata
    """
    info = {"tools": [], "resources": [], "server_info": {}}

    try:
        # Get available tools
        tools_result = await session.list_tools()
        info["tools"] = [
            {"name": tool.name, "description": tool.description}
            for tool in tools_result.tools
        ]
        logger.debug(f"Found {len(info['tools'])} tools")

        # Get available resources
        resources_result = await session.list_resources()
        info["resources"] = [
            {"name": resource.name, "description": resource.description}
            for resource in resources_result.resources
        ]
        logger.debug(f"Found {len(info['resources'])} resources")

        return info

    except Exception as e:
        logger.error(f"Failed to get server info: {e}")
        raise


async def test_connection(
    server_script_path: str = "apps/mcp_server/src/server.py", command: str = "python"
) -> bool:
    """
    Test if we can successfully connect to the MCP server.

    Args:
        server_script_path: Path to the MCP server script
        command: Command to run the server

    Returns:
        True if connection successful, False otherwise
    """
    try:
        async with connect_to_mcp_server(
            server_script_path, command, timeout=10.0
        ) as session:
            await get_server_info(session)
            logger.info("MCP server connection test successful")
            return True
    except Exception as e:
        logger.error(f"MCP server connection test failed: {e}")
        return False
