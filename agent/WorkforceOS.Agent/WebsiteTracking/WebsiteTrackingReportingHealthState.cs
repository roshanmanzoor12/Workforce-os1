namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingReportingHealthState
{
    private readonly object _sync =
        new();

    private long
        _successCount;

    private long
        _failureCount;

    private DateTimeOffset?
        _lastSuccessAt;

    private DateTimeOffset?
        _lastFailureAt;

    private string?
        _lastFailure;

    public void RecordSuccess()
    {
        lock (_sync)
        {
            _successCount++;

            _lastSuccessAt =
                DateTimeOffset.UtcNow;

            _lastFailure =
                null;
        }
    }

    public void RecordFailure(
        string? error
    )
    {
        lock (_sync)
        {
            _failureCount++;

            _lastFailureAt =
                DateTimeOffset.UtcNow;

            _lastFailure =
                error;
        }
    }

    public WebsiteTrackingReportingHealthSnapshot
        Snapshot()
    {
        lock (_sync)
        {
            return new WebsiteTrackingReportingHealthSnapshot(
                SuccessCount:
                    _successCount,

                FailureCount:
                    _failureCount,

                LastSuccessAt:
                    _lastSuccessAt,

                LastFailureAt:
                    _lastFailureAt,

                LastFailure:
                    _lastFailure
            );
        }
    }
}


public sealed record
    WebsiteTrackingReportingHealthSnapshot(
        long SuccessCount,

        long FailureCount,

        DateTimeOffset? LastSuccessAt,

        DateTimeOffset? LastFailureAt,

        string? LastFailure
    );