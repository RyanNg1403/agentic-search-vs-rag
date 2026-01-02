
## Relations
@structure/mcp_client

Tool registry in packages/core/src/tools/tool-registry.ts manages dynamic tool discovery and registration. DiscoveredToolInvocation wraps external tools callable via getToolCallCommand(). Tools discovered from MCP servers are prefixed with DISCOVERED_TOOL_PREFIX. You must use spawn() to execute discovered tools, passing params as JSON via stdin. Tool execution collects stdout/stderr, exit codes, and signals. DiscoveredMCPTool class wraps MCP-sourced tools for registration. The registry pattern enables extensible tool systems where tools can be added at runtime from extensions and MCP servers.
