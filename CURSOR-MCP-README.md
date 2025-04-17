# Deploying MCP Client to Cursor IDE

This guide explains how to deploy the MCP (Model Calling Protocol) client configuration to Cursor IDE.

## Steps to Deploy

1. **Copy the Configuration File**

   Copy the `mcp.json` file to the location where Cursor IDE looks for extensions:

   ```bash
   # For macOS
   cp mcp.json ~/Library/Application\ Support/Cursor/extensions/
   
   # For Windows
   copy mcp.json %APPDATA%\Cursor\extensions\
   
   # For Linux
   cp mcp.json ~/.config/Cursor/extensions/
   ```

2. **Restart Cursor IDE**

   Close and reopen Cursor IDE to load the new configuration.

3. **Check Configuration**

   The MCP functions should now be available in the command palette (Cmd+Shift+P or Ctrl+Shift+P) under "MCP Functions".

## Configuration Explanation

The `mcp.json` file contains:

- **Client Configuration**: Settings for connecting to the MCP server, including URL, endpoints, and retry logic
- **Function Templates**: Pre-defined MCP functions you can call directly from Cursor
- **Code Snippets**: Ready-to-use code examples for interacting with the MCP server

## Customizing the Configuration

You can customize the `mcp.json` file:

1. Update the `server_url` if your MCP server runs on a different host or port
2. Add your API key if authentication is required
3. Create additional function templates for frequently used operations
4. Add or update code snippets with your commonly used patterns

## Troubleshooting

- If functions don't appear in Cursor, check the extensions directory path
- Ensure the MCP server is running when attempting to use the functions
- Check Cursor's developer console (View > Developer > Toggle Developer Tools) for errors 