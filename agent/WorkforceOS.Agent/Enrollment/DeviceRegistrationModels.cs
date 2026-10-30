using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Enrollment;

// =========================================================
// REGISTRATION REQUEST
// =========================================================

public sealed record DeviceRegistrationRequest
{
    [JsonPropertyName("activation_code")]
    public required string ActivationCode { get; init; }

    [JsonPropertyName("hostname")]
    public required string Hostname { get; init; }

    [JsonPropertyName("os_name")]
    public required string OsName { get; init; }

    [JsonPropertyName("os_version")]
    public required string OsVersion { get; init; }

    [JsonPropertyName("architecture")]
    public required string Architecture { get; init; }

    [JsonPropertyName("agent_version")]
    public required string AgentVersion { get; init; }

    [JsonPropertyName("agent_identifier")]
    public required string AgentIdentifier { get; init; }
}


// =========================================================
// DEVICE RESPONSE
// =========================================================

public sealed record RegisteredDevice
{
    [JsonPropertyName("id")]
    public required Guid Id { get; init; }

    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid { get; init; }

    [JsonPropertyName("employee_id")]
    public Guid? EmployeeId { get; init; }

    [JsonPropertyName("hostname")]
    public required string Hostname { get; init; }

    [JsonPropertyName("os_name")]
    public required string OsName { get; init; }

    [JsonPropertyName("os_version")]
    public required string OsVersion { get; init; }

    [JsonPropertyName("architecture")]
    public required string Architecture { get; init; }

    [JsonPropertyName("agent_version")]
    public required string AgentVersion { get; init; }

    [JsonPropertyName("agent_identifier")]
    public string? AgentIdentifier { get; init; }

    [JsonPropertyName("status")]
    public required string Status { get; init; }

    [JsonPropertyName("is_active")]
    public required bool IsActive { get; init; }

    [JsonPropertyName("first_seen_at")]
    public DateTimeOffset? FirstSeenAt { get; init; }

    [JsonPropertyName("last_seen_at")]
    public DateTimeOffset? LastSeenAt { get; init; }

    [JsonPropertyName("registered_at")]
    public DateTimeOffset? RegisteredAt { get; init; }

    [JsonPropertyName("revoked_at")]
    public DateTimeOffset? RevokedAt { get; init; }

    [JsonPropertyName("monitoring_profile_id")]
    public Guid? MonitoringProfileId { get; init; }

    [JsonPropertyName("created_at")]
    public required DateTimeOffset CreatedAt { get; init; }

    [JsonPropertyName("updated_at")]
    public required DateTimeOffset UpdatedAt { get; init; }
}


// =========================================================
// ONE-TIME DEVICE CREDENTIAL
// =========================================================

public sealed record DeviceRegistrationCredential
{
    [JsonPropertyName("device_uuid")]
    public required Guid DeviceUuid { get; init; }

    [JsonPropertyName("device_secret")]
    public required string DeviceSecret { get; init; }
}


// =========================================================
// REGISTRATION RESPONSE
// =========================================================

public sealed record DeviceRegistrationResponse
{
    [JsonPropertyName("message")]
    public required string Message { get; init; }

    [JsonPropertyName("device")]
    public required RegisteredDevice Device { get; init; }

    [JsonPropertyName("credential")]
    public required DeviceRegistrationCredential Credential { get; init; }
}