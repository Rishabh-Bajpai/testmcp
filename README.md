# MCP Client Webapp

This is a simple web application built with Flask that allows you to interact with various Model Context Protocol (MCP) servers. It provides a user interface to discover available tools from configured MCP servers and send commands to them.

## Features

*   **Multi-Server Support:** Configure and interact with multiple MCP servers.
*   **Tool Discovery:** Dynamically fetches and displays tools available from selected MCP servers.
*   **Command Sending:** Provides a form to send commands to the discovered tools.
*   **Structured Output:** Attempts to parse and display command responses in a readable, structured format.

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Rishabh-Bajpai/testmcp.git
cd testmcp
```

### 2. Install Dependencies

This project uses Python. You can install dependencies using `pip` or `conda`.

#### Using Pip

Make sure you have Python 3.8+ installed.

```bash
pip install -r requirements.txt
```

#### Using Conda (Recommended)

If you have Conda installed, you can create a new environment and install dependencies as follows:

```bash
# Optional: Create a separate environment for testing
# conda create -n mcp_test python=3.10 # Or your preferred Python version
# conda activate mcp_test

conda create -n mcp-webapp python=3.10 # Or your preferred Python version
conda activate mcp-webapp
pip install -r requirements.txt
```

### 3. Configure MCP Servers

This application uses a `mcp_config_file.json` to define the MCP servers it can connect to. For security, you should create your own `mcp_config_file.json` based on the example provided.

1.  **Create `mcp_config_file.json`:**
    Copy the example configuration file:
    ```bash
    cp mcp_config_file.json.example mcp_config_file.json
    ```

2.  **Edit `mcp_config_file.json`:**
    Open `mcp_config_file.json` in a text editor. Replace placeholder values like `<YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN>`, `<YOUR_BRAVE_API_KEY>`, etc., with your actual API keys and tokens directly within the `env` block of each server's configuration. **Do not commit your `mcp_config_file.json` to version control!** It is already added to `.gitignore`.

    A typical entry in `mcp_config_file.json` looks like this:
    ```json
    {
      "mcpServers": {
        "Home Assistant": {
          "command": "mcp-proxy",
          "args": [
            "http://homeassistant.local:8123/mcp_server/sse"
          ],
          "env": {
            "API_ACCESS_TOKEN": "YOUR_HOME_ASSISTANT_LONG_LIVED_ACCESS_TOKEN"
          },
          "transport": "stdio"
        }
        // ... other server configurations
      }
    }
    ```

## Running the Webapp

Make sure your MCP servers (like `mcp-proxy`, `mcp-server-fetch`, etc.) are running and accessible as configured in `mcp_config_file.json`.

To start the Flask web application, run:

```bash
python app.py
```

The application will typically run on `http://127.0.0.1:5006`. Open this URL in your web browser.

## Usage

1.  **Select a Server:** Choose an MCP server from the dropdown list.
2.  **Discover Tools:** The available tools for the selected server will be displayed.
3.  **Send Commands:** Click on a tool name to populate the command form. Enter the required arguments and click "Send Command" to interact with the MCP server.

