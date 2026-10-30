using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Api;

public sealed record AppObservationRequest
{
    [JsonPropertyName("process_name")]
    public required string ProcessName { get; init; }

    [JsonPropertyName("executable_path")]
    public string? ExecutablePath { get; init; }

    [JsonPropertyName("window_title")]
    public string? WindowTitle { get; init; }

    [JsonPropertyName("observed_at")]
    public required DateTimeOffset ObservedAt { get; init; }
}


public sealed record AppObservationResponse
{
    [JsonPropertyName("event_id")]
    public required Guid EventId { get; init; }

    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid { get; init; }

    [JsonPropertyName("employee_id")]
    public Guid? EmployeeId { get; init; }

    [JsonPropertyName("app_key")]
    public required string AppKey { get; init; }

    [JsonPropertyName("process_name")]
    public required string ProcessName { get; init; }

    [JsonPropertyName("executable_path")]
    public string? ExecutablePath { get; init; }

    [JsonPropertyName("window_title")]
    public string? WindowTitle { get; init; }

    [JsonPropertyName("observed_at")]
    public required DateTimeOffset ObservedAt { get; init; }

    [JsonPropertyName("received_at")]
    public required DateTimeOffset ReceivedAt { get; init; }
}