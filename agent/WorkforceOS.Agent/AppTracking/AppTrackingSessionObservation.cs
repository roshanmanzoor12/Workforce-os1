using System.Security.Principal;

namespace WorkforceOS.Agent.AppTracking;

public sealed record AppTrackingSessionObservation
{
    public const int CurrentProtocolVersion =
        1;

    public int ProtocolVersion { get; init; } =
        CurrentProtocolVersion;

    public required int SessionId { get; init; }

    public required string UserSid { get; init; }

    public required string ProcessName { get; init; }

    public string? ExecutablePath { get; init; }

    public string? WindowTitle { get; init; }

    public required DateTimeOffset ObservedAt { get; init; }

    public void Validate()
    {
        if (
            ProtocolVersion
            != CurrentProtocolVersion)
        {
            throw new InvalidOperationException(
                $"Unsupported AppTracking protocol version: {ProtocolVersion}.");
        }

        if (SessionId <= 0)
        {
            throw new InvalidOperationException(
                "AppTracking observation must originate from an interactive Windows session.");
        }

        if (string.IsNullOrWhiteSpace(
            UserSid))
        {
            throw new InvalidOperationException(
                "AppTracking observation UserSid is required.");
        }

        _ = new SecurityIdentifier(
            UserSid);

        if (string.IsNullOrWhiteSpace(
            ProcessName))
        {
            throw new InvalidOperationException(
                "AppTracking ProcessName is required.");
        }

        if (ProcessName.Length > 255)
        {
            throw new InvalidOperationException(
                "AppTracking ProcessName exceeds 255 characters.");
        }

        if (
            ExecutablePath is not null
            && ExecutablePath.Length > 4096)
        {
            throw new InvalidOperationException(
                "AppTracking ExecutablePath exceeds 4096 characters.");
        }

        if (
            WindowTitle is not null
            && WindowTitle.Length > 4096)
        {
            throw new InvalidOperationException(
                "AppTracking WindowTitle exceeds 4096 characters.");
        }

        if (ObservedAt == default)
        {
            throw new InvalidOperationException(
                "AppTracking ObservedAt is required.");
        }
    }

    public AppTrackingObservation ToObservation()
    {
        Validate();

        return new AppTrackingObservation
        {
            ProcessName =
                ProcessName.Trim(),

            ExecutablePath =
                string.IsNullOrWhiteSpace(
                    ExecutablePath)
                    ? null
                    : ExecutablePath.Trim(),

            WindowTitle =
                string.IsNullOrWhiteSpace(
                    WindowTitle)
                    ? null
                    : WindowTitle.Trim(),

            ObservedAt =
                ObservedAt,
        };
    }
}