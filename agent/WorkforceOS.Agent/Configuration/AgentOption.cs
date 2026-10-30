using System.ComponentModel.DataAnnotations;

namespace WorkforceOS.Agent.Configuration;

public sealed class AgentOptions
{
    public const string SectionName =
        "Agent";

    // =====================================================
    // BACKEND
    // =====================================================

    [Required]
    [Url]
    public string ApiBaseUrl { get; init; } =
        "http://127.0.0.1:8001";

    // =====================================================
    // API ENDPOINTS
    // =====================================================

    [Required]
    public string RegistrationPath { get; init; } =
        "/api/v1/device-registration/register";

    [Required]
    public string DeviceIdentityPath { get; init; } =
        "/api/v1/device-agent/me";

    // =====================================================
    // HTTP
    // =====================================================

    [Range(
        5,
        300
    )]
    public int HttpTimeoutSeconds { get; init; } =
        30;

    // =====================================================
    // RETRY
    // =====================================================

    [Range(
        1,
        300
    )]
    public int InitialRetryDelaySeconds { get; init; } =
        5;

    [Range(
        5,
        3600
    )]
    public int MaximumRetryDelaySeconds { get; init; } =
        300;

    // =====================================================
    // AGENT
    // =====================================================

    [Required]
    [MinLength(1)]
    [MaxLength(100)]
    public string AgentName { get; init; } =
        "WorkforceOS Agent";

    [Required]
    [MinLength(1)]
    [MaxLength(50)]
    public string AgentVersion { get; init; } =
        "0.1.0";

    // =====================================================
    // OPERATION MODE
    // =====================================================

    public bool MonitoringDisclosureRequired { get; init; } =
        true;
}