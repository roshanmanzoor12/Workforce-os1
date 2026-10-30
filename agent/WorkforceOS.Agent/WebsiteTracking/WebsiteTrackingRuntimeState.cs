namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingRuntimeState
{
    private readonly object _sync =
        new();

    private WebsiteTrackingObservation?
        _latestObservation;

    private DateTimeOffset?
        _latestReceivedAt;

    private long
        _acceptedCount;

    private long
        _rejectedCount;

    public void Accept(
        WebsiteTrackingObservation observation
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        lock (_sync)
        {
            _latestObservation =
                observation;

            _latestReceivedAt =
                DateTimeOffset.UtcNow;

            _acceptedCount++;
        }
    }

    public void Reject()
    {
        lock (_sync)
        {
            _rejectedCount++;
        }
    }

    public WebsiteTrackingRuntimeSnapshot
        Snapshot()
    {
        lock (_sync)
        {
            return new WebsiteTrackingRuntimeSnapshot(
                LatestObservation:
                    _latestObservation,

                LatestReceivedAt:
                    _latestReceivedAt,

                AcceptedCount:
                    _acceptedCount,

                RejectedCount:
                    _rejectedCount
            );
        }
    }
}


public sealed record
    WebsiteTrackingRuntimeSnapshot(
        WebsiteTrackingObservation?
            LatestObservation,

        DateTimeOffset?
            LatestReceivedAt,

        long AcceptedCount,

        long RejectedCount
    );