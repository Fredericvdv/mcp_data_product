import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from logging_config import logger

async def main():
    # Define server parameters
    server_params = StdioServerParameters(
        command="python",  # The command to run your server
        args=["src/mcp_server/server.py"],  # Arguments to the command
    )

    # Connect to the server
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            logger.info("Connected to MCP server and initialized session")

            # List available tools
            tools_result = await session.list_tools()
            logger.info("Available tools:")
            for tool in tools_result.tools:
                logger.info(f"  - {tool.name}: {tool.description}")

            # List available resources
            resources_result = await session.list_resources()
            logger.info("Available resources:")
            for resource in resources_result.resources:
                logger.info(f"  - {resource.name}: {resource.description}")

            # Call our calculator tool
            result = await session.call_tool("add", arguments={"a": 2, "b": 3})
            logger.info(f"Tool execution result: 2 + 3 = {result.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())