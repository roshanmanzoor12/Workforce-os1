using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityBackendReporter
{
    private readonly ActivityReporter
        _activityReporter;

    private readonly ActivityRuntimeState
        _runtimeState;

    private readonly ILogger<ActivityBackendReporter>
        _logger;

    public ActivityBackendReporter(
        ActivityReporter activityReporter,
        ActivityRuntimeState runtimeState,
        ILogger<ActivityBackendReporter> logger
    )
    {
        _activityReporter =
            activityReporter;

        _runtimeState =
            runtimeState;

        _logger =
            logger;
    }

    public async Task<bool> TryReportLatestAsync(
        DeviceCredentials credentials,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        ActivitySessionObservation? observation =
            _runtimeState
                .GetLatestObservation();

        if (
            observation is null
        )
        {
            return false;
        }

        ActivityReceiverHealthSnapshot health =
            _runtimeState
                .GetSnapshot();

        ActivityStateSnapshot snapshot =
            observation
                .ToActivityStateSnapshot();

        if (
            !_activityReporter
                .ShouldReport(
                    snapshot,
                    health.LastReportAt
                )
        )
        {
            return false;
        }

        try
        {
            ActivityStateResponse response =
                await _activityReporter
                    .ReportAsync(
                        credentials,
                        snapshot,
                        cancellationToken
                    );

            _runtimeState.RecordReported(
                response.ReceivedAt
            );

            _logger.LogDebug(
                "Activity observation forwarded to WorkforceOS backend. State={State}, IdleSeconds={IdleSeconds}.",
                response.State,
                response.IdleSeconds
            );

            return true;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            throw;
        }
        catch (
            Exception exception
        )
        {
            _runtimeState.RecordError(
                exception
            );

            _logger.LogWarning(
                exception,
                "Unable to forward current activity observation to WorkforceOS backend."
            );

            return false;
        }
    }
}