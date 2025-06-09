"""
MCP Connection Usage Examples

This module demonstrates various ways to use the MCP connection utilities.
"""

import asyncio

from apps.client.src.logging_config import logger
from apps.client.src.mcp_connection import (
    connect_to_mcp_server,
    get_server_info,
    test_connection,
)


async def example_basic_connection():
    """Example: Basic connection and tool listing."""
    logger.info("=== Basic Connection Example ===")

    async with connect_to_mcp_server() as session:
        server_info = await get_server_info(session)

        logger.info(f"Connected! Found {len(server_info['tools'])} tools")
        for tool in server_info["tools"]:
            logger.info(f"  {tool['name']}: {tool['description']}")


async def example_custom_server_path():
    """Example: Connection with custom server path."""
    logger.info("=== Custom Server Path Example ===")

    # You can specify a different server script
    custom_path = "apps/mcp_server/src/server.py"

    async with connect_to_mcp_server(server_script_path=custom_path) as session:
        tools_result = await session.list_tools()
        logger.info(
            f"Connected to custom server: {len(tools_result.tools)} tools available"
        )


async def example_tool_execution():
    """Example: Executing a tool."""
    logger.info("=== Tool Execution Example ===")

    async with connect_to_mcp_server() as session:
        try:
            # Call the add tool
            result = await session.call_tool("add", arguments={"a": 5, "b": 3})
            logger.info(f"Calculator result: 5 + 3 = {result.content[0].text}")
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")


async def example_resource_access():
    """Example: Accessing server resources."""
    logger.info("=== Resource Access Example ===")

    async with connect_to_mcp_server() as session:
        try:
            # List resources
            resources_result = await session.list_resources()

            if resources_result.resources:
                # Access the first resource
                resource = resources_result.resources[0]
                logger.info(f"Accessing resource: {resource.name}")

                # Read the resource content
                content = await session.read_resource(resource.uri)
                logger.info(
                    f"Resource content preview: {content.contents[0].text[:100]}..."
                )
            else:
                logger.info("No resources available")

        except Exception as e:
            logger.error(f"Resource access failed: {e}")


async def example_connection_testing():
    """Example: Testing connection without full setup."""
    logger.info("=== Connection Testing Example ===")

    # Test if server is reachable
    is_connected = await test_connection()

    if is_connected:
        logger.info("✅ Server connection test passed")
    else:
        logger.error("❌ Server connection test failed")


async def example_error_handling():
    """Example: Proper error handling."""
    logger.info("=== Error Handling Example ===")

    try:
        # Try to connect to a non-existent server
        async with connect_to_mcp_server(
            server_script_path="non_existent_server.py", timeout=5.0
        ) as session:
            await get_server_info(session)

    except ConnectionError as e:
        logger.error(f"Connection failed as expected: {e}")
    except asyncio.TimeoutError:
        logger.error("Connection timed out as expected")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")


async def run_all_examples():
    """Run all examples in sequence."""
    examples = [
        example_basic_connection,
        example_custom_server_path,
        example_tool_execution,
        example_resource_access,
        example_connection_testing,
        example_error_handling,
    ]

    for example_func in examples:
        try:
            await example_func()
            logger.info("✅ Example completed successfully\n")
        except Exception as e:
            logger.error(f"❌ Example failed: {e}\n")


if __name__ == "__main__":
    asyncio.run(run_all_examples())
