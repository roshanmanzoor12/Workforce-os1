namespace WorkforceOS.Agent.AppTracking;

public sealed record AppTrackingHealthSnapshot
{
    public required bool Enabled { get; init; }

    public required bool HasInteractiveObservation { get; init; }

    public required bool HasBackendReport { get; init; }

    public DateTimeOffset? LastReceivedAt { get; init; }

    public DateTimeOffset? LastReportedAt { get; init; }

    public string? CurrentProcessName { get; init; }

    public string? LastError { get; init; }

    public bool IsHealthy =>
        Enabled
        && HasInteractiveObservation
        && string.IsNullOrWhiteSpace(
            LastError);
}