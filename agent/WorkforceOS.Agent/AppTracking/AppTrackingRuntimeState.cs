namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingRuntimeState
{
    private readonly object _sync =
        new();

    private AppTrackingSessionObservation? _latestObservation;

    private DateTimeOffset? _lastReceivedAt;

    private DateTimeOffset? _lastReportedAt;

    private string? _lastError;

    public void RecordObservation(
        AppTrackingSessionObservation observation)
    {
        ArgumentNullException.ThrowIfNull(
            observation);

        lock (_sync)
        {
            _latestObservation =
                observation;

            _lastReceivedAt =
                DateTimeOffset.UtcNow;

            _lastError =
                null;
        }
    }

    public void RecordReported(
        DateTimeOffset reportedAt)
    {
        lock (_sync)
        {
            _lastReportedAt =
                reportedAt;

            _lastError =
                null;
        }
    }

    public void RecordError(
        Exception exception)
    {
        ArgumentNullException.ThrowIfNull(
            exception);

        lock (_sync)
        {
            _lastError =
                exception.Message;
        }
    }

    public AppTrackingRuntimeSnapshot Snapshot()
    {
        lock (_sync)
        {
            return new AppTrackingRuntimeSnapshot
            {
                LatestObservation =
                    _latestObservation,

                LastReceivedAt =
                    _lastReceivedAt,

                LastReportedAt =
                    _lastReportedAt,

                LastError =
                    _lastError,
            };
        }
    }
}


public sealed record AppTrackingRuntimeSnapshot
{
    public AppTrackingSessionObservation? LatestObservation { get; init; }

    public DateTimeOffset? LastReceivedAt { get; init; }

    public DateTimeOffset? LastReportedAt { get; init; }

    public string? LastError { get; init; }
}