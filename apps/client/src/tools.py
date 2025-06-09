from typing import Any, Dict, List

from apps.client.src.logging_config import logger
from apps.client.src.mcp_connection import get_server_info


async def get_mcp_tools(session) -> List[Dict[str, Any]]:
    """Get available MCP tools formatted for OpenAI API.

    Args:
        session: The MCP session.

    Returns:
        List of tools formatted for OpenAI API.
    """
    try:
        server_info = await get_server_info(session)
        tools = []

        for tool in server_info["tools"]:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool.get("inputSchema", {}),
                    },
                }
            )

        return tools
    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        return []
