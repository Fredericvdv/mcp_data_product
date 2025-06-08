from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from logging_config import logger

load_dotenv("../.env")

# Create an MCP server
# mcp = FastMCP(
#     name="Calculator",
#     host="0.0.0.0",  # only used for SSE transport (localhost)
#     port=8050,  # only used for SSE transport (set this to any port)
# )
mcp = FastMCP(name="Fred")
logger.info("Initialized MCP server 'Fred'")


# Add a simple calculator tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    result = a + b
    logger.debug(f"Calculator tool: {a} + {b} = {result}")
    return result

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