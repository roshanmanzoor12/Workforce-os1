using WorkforceOS.Agent.Api;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingBackendReporter
{
    private readonly AppTrackingApiClient _apiClient;

    private readonly AppTrackingRuntimeState _runtimeState;

    private readonly AppTrackingOptions _options;

    private readonly ILogger<AppTrackingBackendReporter> _logger;

    private AppTrackingSessionObservation? _lastReportedObservation;

    public AppTrackingBackendReporter(
        AppTrackingApiClient apiClient,
        AppTrackingRuntimeState runtimeState,
        AppTrackingOptions options,
        ILogger<AppTrackingBackendReporter> logger)
    {
        _apiClient = apiClient;
        _runtimeState = runtimeState;
        _options = options;
        _logger = logger;
    }

    public async Task<bool> ReportLatestAsync(
        Guid deviceUuid,
        string deviceSecret,
        CancellationToken cancellationToken)
    {
        AppTrackingRuntimeSnapshot runtime =
            _runtimeState.Snapshot();

        AppTrackingSessionObservation? observation =
            runtime.LatestObservation;

        if (observation is null)
        {
            return false;
        }

        if (!ShouldReport(
            observation,
            runtime.LastReportedAt))
        {
            return false;
        }

        AppObservationRequest request =
            new()
            {
                ProcessName =
                    observation.ProcessName,

                ExecutablePath =
                    observation.ExecutablePath,

                WindowTitle =
                    _options.CaptureWindowTitles
                        ? observation.WindowTitle
                        : null,

                ObservedAt =
                    observation.ObservedAt,
            };

        AppObservationResponse response =
            await _apiClient.ReportAsync(
                deviceUuid,
                deviceSecret,
                request,
                cancellationToken);

        _runtimeState.RecordReported(
            DateTimeOffset.UtcNow);

        _lastReportedObservation =
            observation;

        _logger.LogDebug(
            "Reported foreground application to WorkforceOS. Process={ProcessName}, EventId={EventId}.",
            observation.ProcessName,
            response.EventId);

        return true;
    }

    private bool ShouldReport(
        AppTrackingSessionObservation observation,
        DateTimeOffset? lastReportedAt)
    {
        if (_lastReportedObservation is null)
        {
            return true;
        }

        bool applicationChanged =
            !string.Equals(
                _lastReportedObservation.ProcessName,
                observation.ProcessName,
                StringComparison.OrdinalIgnoreCase)
            ||
            !string.Equals(
                _lastReportedObservation.ExecutablePath ?? string.Empty,
                observation.ExecutablePath ?? string.Empty,
                StringComparison.OrdinalIgnoreCase);

        if (applicationChanged)
        {
            return true;
        }

        if (lastReportedAt is null)
        {
            return true;
        }

        TimeSpan elapsed =
            DateTimeOffset.UtcNow
            - lastReportedAt.Value;

        return elapsed >=
            TimeSpan.FromSeconds(
                _options.ReportIntervalSeconds);
    }
}