namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingRuntimeCoordinator
{
    private readonly AppTrackingRuntimeState _runtimeState;

    private readonly AppTrackingObservationDeduplicator _deduplicator;

    private readonly ILogger<AppTrackingRuntimeCoordinator> _logger;

    public AppTrackingRuntimeCoordinator(
        AppTrackingRuntimeState runtimeState,
        AppTrackingObservationDeduplicator deduplicator,
        ILogger<AppTrackingRuntimeCoordinator> logger)
    {
        _runtimeState =
            runtimeState;

        _deduplicator =
            deduplicator;

        _logger =
            logger;
    }

    public bool Process(
        AppTrackingSessionObservation observation)
    {
        ArgumentNullException.ThrowIfNull(
            observation);

        observation.Validate();

        if (
            !_deduplicator.ShouldAccept(
                observation))
        {
            _logger.LogDebug(
                "Ignored duplicate or old AppTracking observation. Process={ProcessName}, ObservedAt={ObservedAt}.",
                observation.ProcessName,
                observation.ObservedAt);

            return false;
        }

        _runtimeState.RecordObservation(
            observation);

        _logger.LogDebug(
            "Accepted AppTracking runtime observation. Process={ProcessName}, ObservedAt={ObservedAt}.",
            observation.ProcessName,
            observation.ObservedAt);

        return true;
    }
}