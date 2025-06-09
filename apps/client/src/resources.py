from typing import Any, Dict, List

from apps.client.src.logging_config import logger
from apps.client.src.mcp_connection import get_server_info


async def get_mcp_resources(session) -> List[Dict[str, Any]]:
    """Get available MCP resources formatted for OpenAI API.

    Args:
        session: The MCP session.

    Returns:
        List of resources formatted for OpenAI API.
    """
    try:
        server_info = await get_server_info(session)
        resources = []

        for resource in server_info["resources"]:
            resources.append(
                {
                    "type": "resource",
                    "resource": {
                        "name": resource["name"],
                        "description": resource["description"],
                    },
                }
            )

        return resources
    except Exception as e:
        logger.error(f"Error getting MCP resources: {e}")
        return []


async def get_resources_content(session) -> dict:
    """Fetch the actual content of available MCP resources.

    Args:
        session: The MCP session.

    Returns:
        Dictionary mapping resource names to their content.
    """
    resources_content = {}
    try:
        # List available resources
        resources_result = await session.list_resources()

        # Fetch content for each resource
        for resource in resources_result.resources:
            try:
                logger.info(f"Fetching content for resource: {resource.name}")
                content_result = await session.read_resource(resource.uri)

                # Extract text content
                if content_result.contents:
                    content_text = ""
                    for content in content_result.contents:
                        if hasattr(content, "text"):
                            content_text += content.text + "\n"

                    resources_content[resource.name] = content_text.strip()

            except Exception as e:
                logger.warning(
                    f"Could not fetch content for resource {resource.name}: {e}"
                )
                resources_content[resource.name] = f"[Content unavailable: {str(e)}]"

    except Exception as e:
        logger.error(f"Error fetching resources content: {e}")

    return resources_content
