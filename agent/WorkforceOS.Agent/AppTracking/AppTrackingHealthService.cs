namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingHealthService
{
    private readonly AppTrackingRuntimeState _runtimeState;

    private readonly AppTrackingOptions _options;

    public AppTrackingHealthService(
        AppTrackingRuntimeState runtimeState,
        AppTrackingOptions options)
    {
        _runtimeState =
            runtimeState;

        _options =
            options;
    }

    public AppTrackingHealthSnapshot GetSnapshot()
    {
        AppTrackingRuntimeSnapshot runtime =
            _runtimeState.Snapshot();

        return new AppTrackingHealthSnapshot
        {
            Enabled =
                _options.Enabled,

            HasInteractiveObservation =
                runtime.LatestObservation
                is not null,

            HasBackendReport =
                runtime.LastReportedAt
                is not null,

            LastReceivedAt =
                runtime.LastReceivedAt,

            LastReportedAt =
                runtime.LastReportedAt,

            CurrentProcessName =
                runtime
                    .LatestObservation?
                    .ProcessName,

            LastError =
                runtime.LastError,
        };
    }
}