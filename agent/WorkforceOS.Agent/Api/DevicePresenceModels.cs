using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Api;

public sealed record DevicePresenceResponse
{
    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    [JsonPropertyName("is_online")]
    public required bool IsOnline
    {
        get;
        init;
    }

    [JsonPropertyName("last_seen_at")]
    public DateTimeOffset? LastSeenAt
    {
        get;
        init;
    }

    [JsonPropertyName("offline_since")]
    public DateTimeOffset? OfflineSince
    {
        get;
        init;
    }

    [JsonPropertyName("online_timeout_seconds")]
    public required int OnlineTimeoutSeconds
    {
        get;
        init;
    }
}