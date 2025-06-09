import asyncio

from apps.client.src.logging_config import logger
from apps.client.src.mcp_connection import connect_to_mcp_server
from apps.client.src.queries import process_query_with_resource_tools


async def main():
    """
    Main application entry point.
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
