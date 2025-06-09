import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from apps.client.src.logging_config import logger

load_dotenv("../.env")

mcp = FastMCP(name="Fred")
logger.info("Initialized MCP server 'Fred'")


# Add a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    result = a + b
    logger.debug(f"Calculator tool: {a} + {b} = {result}")
    return result


@mcp.tool()
def read_resource_content(resource_uri: str) -> str:
    """Read the content of a specific MCP resource by its URI.

    Args:
        resource_uri: The URI of the resource to read (e.g., 'data://list', 'config://app', 'greeting://user')

    Returns:
        The content of the requested resource
    """
    logger.debug(f"Reading resource content for URI: {resource_uri}")

    try:
        # Handle different resource types
        if resource_uri == "data://list":
            return list_all_data_products()
        elif resource_uri == "data://list_all_data_products":
            return list_all_data_products()
        elif resource_uri == "config://app":
            return get_config()
        elif resource_uri == "config://get_config":
            return get_config()
        elif resource_uri.startswith("greeting://"):
            # Extract name from greeting URI
            name = resource_uri.replace("greeting://", "")
            return get_greeting(name)
        else:
            return f"Unknown resource URI: {resource_uri}"

    except Exception as e:
        logger.error(f"Error reading resource {resource_uri}: {str(e)}")
        return f"Error reading resource {resource_uri}: {str(e)}"


@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    logger.debug("Serving configuration resource")
    return "App configuration here"


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    logger.debug(f"Generating greeting for: {name}")
    return f"Hello, {name}!"


@mcp.resource("data://list")
def list_all_data_products() -> str:
    """List all available data product names"""
    logger.debug("Listing all data products")

    resources_path = "resources"
    try:
        # Get all directories in the resources folder
        if os.path.exists(resources_path):
            data_products = [
                item
                for item in os.listdir(resources_path)
                if os.path.isdir(os.path.join(resources_path, item))
            ]

            if data_products:
                result = "Available Data Products:\n" + "\n".join(
                    f"- {dp}" for dp in sorted(data_products)
                )
                logger.debug(f"Found {len(data_products)} data products")
                return result
            else:
                return "No data products found in the resources directory."
        else:
            logger.warning(f"Resources directory not found at: {resources_path}")
            return "Resources directory not found."

    except Exception as e:
        logger.error(f"Error listing data products: {str(e)}")
        return f"Error accessing data products: {str(e)}"


# Run the server
if __name__ == "__main__":
    transport = "stdio"
    if transport == "stdio":
        logger.info("Starting MCP server with stdio transport")
        mcp.run(transport="stdio")
    elif transport == "sse":
        logger.info("Starting MCP server with SSE transport")
        mcp.run(transport="sse")
    else:
        logger.error(f"Unknown transport: {transport}")
        raise ValueError(f"Unknown transport: {transport}")
