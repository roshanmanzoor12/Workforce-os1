using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Api;

// =========================================================
// HEARTBEAT REQUEST
// =========================================================

public sealed record DeviceHeartbeatRequest
{
    [JsonPropertyName("agent_version")]
    public string? AgentVersion
    {
        get;
        init;
    }

    [JsonPropertyName("hostname")]
    public string? Hostname
    {
        get;
        init;
    }
}


// =========================================================
// HEARTBEAT RESPONSE
// =========================================================

public sealed record DeviceHeartbeatResponse
{
    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    [JsonPropertyName("status")]
    public required string Status
    {
        get;
        init;
    }

    [JsonPropertyName("heartbeat_at")]
    public required DateTimeOffset HeartbeatAt
    {
        get;
        init;
    }

    [JsonPropertyName("next_heartbeat_seconds")]
    public required int NextHeartbeatSeconds
    {
        get;
        init;
    }
}