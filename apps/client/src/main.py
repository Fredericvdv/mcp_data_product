import asyncio

from apps.client.src.logging_config import logger
from apps.client.src.mcp_connection import connect_to_mcp_server
from apps.client.src.queries import process_query_with_resource_tools


async def main():
    """
    Main application entry point.

    Connects to the MCP server and demonstrates basic functionality.

    Two approaches for handling MCP resources with OpenAI:

    1. process_query() - Fetches all resource content upfront and includes it in the system message.
       Pros: LLM has immediate access to all resource content
       Cons: Can make the context very large with many/large resources

    2. process_query_with_resource_tools() - Only provides resource metadata initially,
       LLM uses tools to fetch specific content on demand.
       Pros: More efficient, LLM fetches only what it needs
       Cons: Requires additional API calls to get resource content
    """
    try:
        # Connect to the server using the utility function
        async with connect_to_mcp_server() as session:
            test_query = "What data products are available to me?"
            response = await process_query_with_resource_tools(session, test_query)
            logger.info(f"Query: {test_query}")
            logger.info(f"Response: {response}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
