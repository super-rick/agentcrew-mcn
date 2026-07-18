"""
Tool format adapter — bidirectional conversion between AgentCrew Tools and MCP tool definitions.

AgentCrew Tool.parameters is a complete JSON Schema:
    {"type": "object", "properties": {...}, "required": [...]}

MCP inputSchema is the same JSON Schema object — no structural transformation needed.
The key difference: MCP tool execution is async (needs an MCP session),
while AgentCrew Tool.func is synchronous. We bridge this via asyncio.run().

This module has NO dependency on the MCP SDK — it operates on plain dicts.
"""

from __future__ import annotations

from typing import Any, Callable

from agents.tools import Tool


def agentcrew_tool_to_mcp_tool(tool: Tool) -> dict[str, Any]:
    """Convert an AgentCrew Tool to MCP tool definition format.

    Args:
        tool: An AgentCrew Tool instance.

    Returns:
        MCP-compatible tool definition dict:
            {"name": str, "description": str, "inputSchema": dict}
    """
    return {
        "name": tool.name,
        "description": tool.description,
        "inputSchema": tool.parameters,
    }


def mcp_tool_to_agentcrew_tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    execute_fn: Callable[..., Any],
) -> Tool:
    """Convert an MCP tool definition to an AgentCrew Tool.

    Args:
        name: Tool name from MCP server.
        description: Tool description from MCP server.
        input_schema: JSON Schema for tool parameters (from MCP list_tools).
        execute_fn: A synchronous callable that executes the MCP tool.
                    Typically wraps MCP session.call_tool() via asyncio.run().

    Returns:
        An AgentCrew Tool instance whose .func delegates to the MCP tool.
    """
    # MCP inputSchema is already a JSON Schema, same as Tool.parameters format.
    # Ensure it's wrapped with type: "object" if the server omits it.
    parameters = _normalize_input_schema(input_schema)

    return Tool(
        name=name,
        description=description,
        parameters=parameters,
        func=execute_fn,
    )


def _normalize_input_schema(input_schema: dict[str, Any]) -> dict[str, Any]:
    """Ensure input_schema has the standard JSON Schema structure.

    Some MCP servers provide {'properties': {...}, 'required': [...]}
    without the top-level 'type': 'object'. We add it for consistency
    with AgentCrew's Tool.parameters format.
    """
    if not input_schema:
        return {"type": "object", "properties": {}}

    normalized = dict(input_schema)

    # Add type if missing
    if "type" not in normalized:
        normalized["type"] = "object"

    # Ensure properties dict exists
    if "properties" not in normalized:
        normalized["properties"] = {}

    return normalized
