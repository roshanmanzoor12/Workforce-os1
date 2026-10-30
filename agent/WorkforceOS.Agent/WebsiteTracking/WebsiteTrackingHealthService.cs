namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingHealthService
{
    private readonly
        WebsiteTrackingRuntimeState
        _runtimeState;

    public WebsiteTrackingHealthService(
        WebsiteTrackingRuntimeState
            runtimeState
    )
    {
        _runtimeState =
            runtimeState;
    }

    public WebsiteTrackingHealthSnapshot
        GetSnapshot()
    {
        WebsiteTrackingRuntimeSnapshot state =
            _runtimeState
                .Snapshot();

        return new WebsiteTrackingHealthSnapshot(
            HasObservation:
                state.LatestObservation
                is not null,

            BrowserProcessName:
                state
                    .LatestObservation?
                    .BrowserProcessName,

            Domain:
                state
                    .LatestObservation?
                    .Domain,

            LastObservedAt:
                state
                    .LatestObservation?
                    .ObservedAt,

            LastReceivedAt:
                state
                    .LatestReceivedAt,

            AcceptedCount:
                state.AcceptedCount,

            RejectedCount:
                state.RejectedCount
        );
    }
}


public sealed record WebsiteTrackingHealthSnapshot(
    bool HasObservation,

    string? BrowserProcessName,

    string? Domain,

    DateTimeOffset? LastObservedAt,

    DateTimeOffset? LastReceivedAt,

    long AcceptedCount,

    long RejectedCount
);