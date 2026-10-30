using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Api;

public sealed record ActivityStateRequest
{
    [JsonPropertyName("state")]
    public required string State
    {
        get;
        init;
    }

    [JsonPropertyName("idle_seconds")]
    public required int IdleSeconds
    {
        get;
        init;
    }

    [JsonPropertyName("last_input_at")]
    public DateTimeOffset? LastInputAt
    {
        get;
        init;
    }

    [JsonPropertyName("observed_at")]
    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }
}


public sealed record ActivityStateResponse
{
    [JsonPropertyName("event_id")]
    public required Guid EventId
    {
        get;
        init;
    }

    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    [JsonPropertyName("employee_id")]
    public Guid? EmployeeId
    {
        get;
        init;
    }

    [JsonPropertyName("state")]
    public required string State
    {
        get;
        init;
    }

    [JsonPropertyName("idle_seconds")]
    public required int IdleSeconds
    {
        get;
        init;
    }

    [JsonPropertyName("last_input_at")]
    public DateTimeOffset? LastInputAt
    {
        get;
        init;
    }

    [JsonPropertyName("observed_at")]
    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }

    [JsonPropertyName("received_at")]
    public required DateTimeOffset ReceivedAt
    {
        get;
        init;
    }
}


public sealed record ActivityStatusResponse
{
    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    [JsonPropertyName("employee_id")]
    public Guid? EmployeeId
    {
        get;
        init;
    }

    [JsonPropertyName("state")]
    public required string State
    {
        get;
        init;
    }

    [JsonPropertyName("idle_seconds")]
    public required int IdleSeconds
    {
        get;
        init;
    }

    [JsonPropertyName("last_input_at")]
    public DateTimeOffset? LastInputAt
    {
        get;
        init;
    }

    [JsonPropertyName("observed_at")]
    public DateTimeOffset? ObservedAt
    {
        get;
        init;
    }

    [JsonPropertyName("received_at")]
    public DateTimeOffset? ReceivedAt
    {
        get;
        init;
    }
}