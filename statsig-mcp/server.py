#!/usr/bin/env python3

import asyncio
import json
import os
import sys
from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Import the main function
from main import create_experiment


class StatsigMCPServer:
    def __init__(self):
        self.server = Server("statsig-server")
        self.setup_handlers()

    def setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available tools."""
            return [
                types.Tool(
                    name="create_experiment",
                    description="Creates and automatically starts a new Statsig experiment. The experiment will be created and then immediately started so it can run in your webapp. For the name, use either the component you are modifying (e.g., 'button') or the general idea behind the test (e.g., 'selling') in kebab-case format. CRITICAL: Change ONLY ONE parameter across all groups (e.g., ONLY color OR ONLY text, never multiple parameters). CRITICAL: The experiment name changes! Check the response json to find the new experiment name for use in your program. Each group's description field MUST be actual code, not text descriptions. The group description should be the exact code/HTML that would render when that group's parameters are applied.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the experiment in kebab-case. Use either the component you are modifying (e.g., 'button') or the general idea behind the test (e.g., 'selling'). A UUID will be automatically appended to ensure uniqueness."
                            },
                            "description": {
                                "type": "string",
                                "description": "Describes what the experiment is testing for."
                            },
                            "groups": {
                                "type": "array",
                                "description": "List of groups (variants) in the experiment. Each group defines its share of users and parameter values.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "description": "The group name (e.g., 'Control', 'Treatment')."
                                        },
                                        "description": {
                                            "type": "string",
                                            "description": "MUST BE ACTUAL CODE/HTML - NOT text description. Provide the exact code snippet that would render when this group's parameters are applied (e.g., '<button style=\"color: blue\">Click me</button>')."
                                        },
                                        "parameterValues": {
                                            "type": "object",
                                            "description": "A dictionary of parameter names and their values for this group.",
                                            "additionalProperties": True
                                        }
                                    },
                                    "required": ["name", "parameterValues"]
                                }
                            }
                        },
                        "required": ["name", "description", "groups"]
                    },
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
            """Handle tool execution requests."""
            if name == "create_experiment":
                return await self._create_experiment(arguments)
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"Error: Unknown tool '{name}'"
                    )
                ]

    async def _create_experiment(self, arguments: dict | None) -> list[types.TextContent]:
        """Create a Statsig experiment."""
        try:
            # Get the API key from environment variable
            api_key = os.getenv("STATSIG_API_KEY")
            if not api_key:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: STATSIG_API_KEY environment variable is not set. Please provide your Statsig Console API key."
                    )
                ]
            
            # Validate required arguments
            if not arguments:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Missing required arguments. Please provide 'name', 'description' and 'groups'."
                    )
                ]
            
            name = arguments.get("name")
            description = arguments.get("description")
            groups = arguments.get("groups")
            
            if not name:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Missing required argument 'name'."
                    )
                ]
            
            if not description:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Missing required argument 'description'."
                    )
                ]
            
            if not groups:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: Missing required argument 'groups'."
                    )
                ]
            
            # Validate groups structure
            if not isinstance(groups, list) or len(groups) == 0:
                return [
                    types.TextContent(
                        type="text",
                        text="Error: 'groups' must be a non-empty list."
                    )
                ]
            
            # Note: Group sizes will be automatically calculated and distributed evenly
            
            # Call the create_experiment function from main.py
            result = create_experiment(api_key, name, description, groups)
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Successfully created Statsig experiment!\n\nExperiment Details:\n{json.dumps(result, indent=2)}"
                )
            ]
        
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error creating experiment: {str(e)}"
                )
            ]

    async def run(self):
        """Run the MCP server."""
        # Use stdin/stdout for communication with MCP client
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="statsig-server",
                    server_version="0.1.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )


async def main():
    """Main entry point."""
    server = StatsigMCPServer()
    await server.run()


if __name__ == "__main__":
    # When run directly, we expect to be called by an MCP client
    # The server will wait for MCP protocol messages on stdin
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This is expected when stopping the server
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)
