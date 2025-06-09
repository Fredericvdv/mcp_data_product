import json
import os
import traceback
from typing import Any, Dict, List, Optional

import openai

from apps.client.src.logging_config import logger
from apps.client.src.resources import get_mcp_resources
from apps.client.src.tools import get_mcp_tools

# TODO: These should be imported from a config module
# For now, assuming they exist in the global scope
# openai_client and model should be properly imported/configured

# Constants
SYSTEM_MESSAGE_BASE = "You are a helpful assistant."
RESOURCES_PROMPT = "\n\nAvailable Resources (use tools to fetch content):\n"
TOOL_USAGE_PROMPT = "\nUse the appropriate tools to fetch resource content when needed."
TOOL_CHOICE_AUTO = "auto"
TOOL_CHOICE_NONE = "none"

# Environment setup
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    logger.error("OPENAI_API_KEY not found in environment variables")
    raise ValueError("OPENAI_API_KEY environment variable is required")

# OpenAI client setup
openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
model = "gpt-4"  # You can change this to gpt-3.5-turbo or other models as needed


def _build_system_message(resources_info: Optional[List[Dict[str, Any]]]) -> str:
    """Build the system message with available resources information.

    Args:
        resources_info: List of resource information dictionaries.

    Returns:
        The formatted system message string.
    """
    system_message = SYSTEM_MESSAGE_BASE

    if resources_info:
        system_message += RESOURCES_PROMPT
        for resource in resources_info:
            name = resource["resource"]["name"]
            description = resource["resource"]["description"]
            system_message += f"- {name}: {description}\n"
        system_message += TOOL_USAGE_PROMPT

    return system_message


def _log_resources_info(resources_info: Optional[List[Dict[str, Any]]]) -> None:
    """Log information about available resources.

    Args:
        resources_info: List of resource information dictionaries.
    """
    logger.info(f"Retrieved {len(resources_info) if resources_info else 0} resources")
    if resources_info:
        resource_names = [resource["resource"]["name"] for resource in resources_info]
        logger.info(f"Available resources: {resource_names}")


def _log_tools_info(tools: Optional[List[Dict[str, Any]]]) -> None:
    """Log information about available tools.

    Args:
        tools: List of tool dictionaries.
    """
    tool_names = (
        [tool.get("function", {}).get("name", "unknown") for tool in tools]
        if tools
        else "None"
    )
    logger.info(f"Retrieved {len(tools) if tools else 0} tools: {tool_names}")


def _log_assistant_response(assistant_message) -> None:
    """Log information about the assistant's response.

    Args:
        assistant_message: The assistant's message object.
    """
    content_preview = (assistant_message.content or "None")[:100]
    logger.info(f"Assistant message content preview: {content_preview}...")
    logger.info(f"Tool calls present: {assistant_message.tool_calls is not None}")

    if assistant_message.tool_calls:
        tool_call_names = [tc.function.name for tc in assistant_message.tool_calls]
        logger.info(f"Tool calls requested: {tool_call_names}")


async def _execute_single_tool_call(
    session, tool_call, index: int, total: int
) -> Dict[str, str]:
    """Execute a single tool call and return the result message.

    Args:
        session: The MCP session.
        tool_call: The tool call object.
        index: Current tool call index (0-based).
        total: Total number of tool calls.

    Returns:
        Dictionary with role, tool_call_id, and content for the message.
    """
    try:
        logger.info(f"Executing tool {index+1}/{total}: {tool_call.function.name}")
        logger.debug(f"Tool arguments: {tool_call.function.arguments}")

        # Parse and log the arguments
        parsed_args = json.loads(tool_call.function.arguments)
        logger.info(f"Parsed tool arguments: {parsed_args}")

        # Execute tool call
        result = await session.call_tool(
            tool_call.function.name,
            arguments=parsed_args,
        )

        logger.info(f"Tool {tool_call.function.name} executed successfully")
        logger.debug(f"Tool result preview: {str(result.content[0].text)[:200]}...")
        logger.info(f"Full tool result content: {result.content[0].text}")

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result.content[0].text,
        }

    except Exception as e:
        logger.error(f"Error executing tool {tool_call.function.name}: {e}")
        logger.error(f"Tool arguments were: {tool_call.function.arguments}")

        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": f"Error executing tool: {str(e)}",
        }


async def _process_tool_calls(
    session, assistant_message, messages: List[Dict[str, Any]]
) -> None:
    """Process all tool calls from the assistant's response.

    Args:
        session: The MCP session.
        assistant_message: The assistant's message with tool calls.
        messages: The conversation messages list to append tool results to.
    """
    tool_calls = assistant_message.tool_calls
    logger.info(f"Processing {len(tool_calls)} tool call(s)")

    # Process each tool call
    for i, tool_call in enumerate(tool_calls):
        tool_result_message = await _execute_single_tool_call(
            session, tool_call, i, len(tool_calls)
        )
        messages.append(tool_result_message)


async def _make_openai_call(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]],
    tool_choice: str,
    call_type: str,
) -> Any:
    """Make a call to the OpenAI API.

    Args:
        messages: List of conversation messages.
        tools: Available tools for the API.
        tool_choice: Tool choice setting for the API.
        call_type: Description of the call type for logging.

    Returns:
        The OpenAI API response.
    """
    logger.info(f"Making {call_type} OpenAI API call...")
    logger.debug(f"Using model: {model}")
    logger.debug(f"Tools available: {tools is not None}")
    logger.debug(f"Number of messages: {len(messages)}")

    response = await openai_client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools if tools else None,
        tool_choice=tool_choice if tools else None,
    )

    logger.info(f"Received response from OpenAI ({call_type})")
    return response


async def process_query_with_resource_tools(session, query: str) -> str:
    """Process a query using OpenAI with MCP tools and on-demand resource fetching.

    This version only provides resource metadata initially and fetches content on demand.

    Args:
        session: The MCP session.
        query: The user query.

    Returns:
        The response from OpenAI.
    """
    try:
        logger.info(f"Starting query processing: {query}")

        # Get available tools and resources
        logger.info("Fetching available MCP tools...")
        tools = await get_mcp_tools(session)
        _log_tools_info(tools)

        logger.info("Fetching available MCP resources metadata...")
        resources_info = await get_mcp_resources(session)
        _log_resources_info(resources_info)

        # Build system message and conversation
        system_message = _build_system_message(resources_info)
        logger.info(f"System message length: {len(system_message)} characters")
        logger.debug(f"System message: {system_message}")

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": query},
        ]

        # Make initial OpenAI API call
        response = await _make_openai_call(messages, tools, TOOL_CHOICE_AUTO, "initial")

        # Process assistant's response
        assistant_message = response.choices[0].message
        _log_assistant_response(assistant_message)
        messages.append(assistant_message)

        # Handle tool calls if present
        if assistant_message.tool_calls:
            await _process_tool_calls(session, assistant_message, messages)

            # Get final response from OpenAI with tool results
            final_response = await _make_openai_call(
                messages, tools, TOOL_CHOICE_NONE, "final"
            )

            final_content = final_response.choices[0].message.content
            logger.info(f"Final response preview: {(final_content or 'None')[:100]}...")
            return final_content

        # No tool calls, return direct response
        logger.info("No tool calls were made, returning direct response")
        direct_content = assistant_message.content
        logger.info(f"Direct response preview: {(direct_content or 'None')[:100]}...")
        return direct_content

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return f"Sorry, I encountered an error while processing your query: {str(e)}"
