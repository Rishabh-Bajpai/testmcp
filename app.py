import os
import json
import asyncio
from typing import List, Dict, Any
import yaml
from langchain.tools.render import render_text_description
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Global variables to store MCP client and tools
# We will now store the full config and dynamically create clients
ALL_MCP_SERVERS_CONFIG: Dict[str, Any] = {}

# This will store active MCP clients, keyed by server name
ACTIVE_MCP_CLIENTS: Dict[str, MultiServerMCPClient] = {}
ACTIVE_MCP_TOOLS: Dict[str, List[BaseTool]] = {}

MCP_CONFIG_FILE = "mcp_config_file.json"

def load_mcp_servers_config():
    global ALL_MCP_SERVERS_CONFIG
    try:
        with open(MCP_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            ALL_MCP_SERVERS_CONFIG = config.get("mcpServers", {})
        print(f"Loaded {len(ALL_MCP_SERVERS_CONFIG)} MCP server configurations.")
    except FileNotFoundError:
        print(f"Error: {MCP_CONFIG_FILE} not found.")
        ALL_MCP_SERVERS_CONFIG = {}
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {MCP_CONFIG_FILE}.")
        ALL_MCP_SERVERS_CONFIG = {}

async def get_or_initialize_mcp_client(server_name: str) -> MultiServerMCPClient | None:
    global ACTIVE_MCP_CLIENTS, ACTIVE_MCP_TOOLS

    if server_name in ACTIVE_MCP_CLIENTS:
        return ACTIVE_MCP_CLIENTS[server_name]

    server_config = ALL_MCP_SERVERS_CONFIG.get(server_name)

    if not server_config:
        print(f"Error: Server '{server_name}' not found in configuration.")
        return None

    # Ensure env vars are directly used from config, no more .env or os.getenv
    # The config should contain the actual tokens now.
    # If a placeholder is still present, it means the user hasn't updated their config.
    if "env" in server_config:
        for key, value in server_config["env"].items():
            if isinstance(value, str) and "<YOUR_" in value and ">" in value:
                print(f"WARNING: Placeholder '{value}' found for {key} in {server_name} config. Please replace with actual token.")
                return None # Or handle more gracefully, e.g., by skipping this server

    # Create a client for only this specific server
    client_config_for_single_server = {server_name: server_config}
    client = MultiServerMCPClient(client_config_for_single_server)

    try:
        tools = await client.get_tools()
        ACTIVE_MCP_CLIENTS[server_name] = client
        ACTIVE_MCP_TOOLS[server_name] = tools
        print(f"Successfully initialized client and fetched {len(tools)} tools for '{server_name}'.")
        return client
    except Exception as e:
        print(f"Error initializing client or fetching tools for '{server_name}': {e}")
        return None



@app.route('/')
async def index():
    return render_template('index.html')

@app.route('/servers')
def get_servers():
    return jsonify(list(ALL_MCP_SERVERS_CONFIG.keys()))

@app.route('/tools')
async def get_tools():
    server_name = request.args.get('server')
    if not server_name:
        return jsonify({"error": "Server name is required."}), 400

    client = await get_or_initialize_mcp_client(server_name)
    if not client:
        return jsonify({"error": f"Failed to initialize client for {server_name}."}), 500

    tools = ACTIVE_MCP_TOOLS.get(server_name, [])
    tool_data = []
    for tool in tools:
        tool_data.append({
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_schema if tool.args_schema else {}
        })
    return jsonify(tool_data)

@app.route('/send_command', methods=['POST'])
async def send_command():
    data = request.get_json()
    server_name = data.get('server_name')
    tool_name = data.get('tool_name')
    args = data.get('args', {})

    if not server_name:
        return jsonify({"error": "Server name is required."}), 400
    if not tool_name:
        return jsonify({"error": "Tool name is required."}), 400

    client = ACTIVE_MCP_CLIENTS.get(server_name)
    if not client:
        # Attempt to initialize if not already active
        client = await get_or_initialize_mcp_client(server_name)
        if not client:
            return jsonify({"error": f"Failed to initialize client for {server_name}."}), 500

    tools = ACTIVE_MCP_TOOLS.get(server_name, [])
    tool_to_execute = next((t for t in tools if t.name == tool_name), None)

    if not tool_to_execute:
        return jsonify({"error": f"Tool '{tool_name}' not found for server '{server_name}'."}), 404

    try:
        # Always pass the arguments as tool_input, let the tool handle parsing
        result = await tool_to_execute.arun(tool_input=args)

        # Attempt to unescape the string if it contains escaped newlines
        if isinstance(result, str) and '\n' in result:
            # First, unescape the backslashes to get actual newlines
            # This handles the case where the string is double-escaped
            unescaped_string = result.replace('\n', '\n')
            
            # Try to extract the YAML part
            yaml_start_index = unescaped_string.find('- names:')
            if yaml_start_index != -1:
                yaml_string = unescaped_string[yaml_start_index:]
                try:
                    # Try to parse as YAML
                    parsed_yaml = yaml.safe_load(yaml_string)
                    result = parsed_yaml
                except yaml.YAMLError:
                    # If not valid YAML, keep as the unescaped string
                    result = unescaped_string # Keep the unescaped string for display
            else:
                # If no YAML part found, keep as the unescaped string
                result = unescaped_string

        return jsonify({"success": True, "result": result})
    except Exception as e:
        print(f"Error executing tool '{tool_name}': {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    load_mcp_servers_config()
    app.run(debug=True, port=5006)