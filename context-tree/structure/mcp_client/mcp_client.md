
## Relations
@authentication/oauth2
@authentication/mcp_oauth

MCP client implementation in packages/core/src/tools/mcp-client.ts connects to MCP servers using @modelcontextprotocol/sdk. MCPClient class supports three transport types: StdioClientTransport (stdio), SSEClientTransport (SSE), StreamableHTTPClientTransport (HTTP). You must configure MCPServerConfig with transport type, command, args, and optional auth. Authentication providers: GoogleCredentialProvider (Google auth), ServiceAccountImpersonationProvider (SA impersonation), MCPOAuthProvider (OAuth2). Connection status tracked via MCPServerStatus enum (DISCONNECTED, CONNECTING, CONNECTED, DISCONNECTING). Tools discovered via listTools() are wrapped in DiscoveredMCPTool. Default timeout is MCP_DEFAULT_TIMEOUT_MSEC (10 minutes).
