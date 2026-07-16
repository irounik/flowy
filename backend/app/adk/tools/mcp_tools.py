"""MCP tool integration for workflow nodes."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MCPToolClient:
    """Lightweight MCP client stub for MVP filesystem operations."""

    async def call_tool(self, server: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        logger.info(
            "mcp tool call",
            extra={"server": server, "tool_name": tool_name, "arguments": arguments},
        )

        if server == "filesystem" and tool_name == "read_file":
            path = arguments.get("path", "")
            return {
                "server": server,
                "tool": tool_name,
                "result": f"[MVP stub] Contents of {path}",
            }

        if server == "filesystem" and tool_name == "list_directory":
            path = arguments.get("path", ".")
            return {
                "server": server,
                "tool": tool_name,
                "result": [f"{path}/file1.txt", f"{path}/file2.txt"],
            }

        return {
            "server": server,
            "tool": tool_name,
            "result": f"MCP stub response for {tool_name}",
        }


mcp_client = MCPToolClient()
