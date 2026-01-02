
## Relations
@structure/tool_registry
@authentication/oauth2
@testing/telemetry

Config system in packages/core/src/config/config.ts is the central configuration hub managing all CLI subsystems. Config class provides getters for: ToolRegistry, PromptRegistry, ResourceRegistry, ContentGenerator, HookSystem, PolicyEngine, MessageBus, AgentRegistry, ModelConfigService, FileSystemService, and more. You must call initialize() to set up registries and load MCP servers. Authentication via getOauthClient() with AuthType enum. Telemetry initialization via initializeTelemetry() with configurable targets (GCP, OTLP, file). Settings include TelemetrySettings, AccessibilitySettings, OutputSettings, CodebaseInvestigatorSettings. WorkspaceContext tracks file/folder subscriptions. Always use config.getTargetDir() for path resolution.
