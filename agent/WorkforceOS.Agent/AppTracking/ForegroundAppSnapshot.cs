namespace WorkforceOS.Agent.AppTracking;

public sealed record ForegroundAppSnapshot
{
    public required string ProcessName { get; init; }

    public string? ExecutablePath { get; init; }

    public string? WindowTitle { get; init; }

    public required DateTimeOffset ObservedAt { get; init; }

    public int ProcessId { get; init; }
}