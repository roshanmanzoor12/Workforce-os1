using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityReporter
{
    private readonly ActivityApiClient
        _apiClient;

    private readonly ActivityOptions
        _options;

    private readonly ILogger<ActivityReporter>
        _logger;

    private ActivityStateSnapshot?
        _lastReportedSnapshot;

    public ActivityReporter(
        ActivityApiClient apiClient,
        IOptions<ActivityOptions> options,
        ILogger<ActivityReporter> logger
    )
    {
        _apiClient =
            apiClient;

        _options =
            options.Value;

        _logger =
            logger;
    }

    public async Task<ActivityStateResponse>
        ReportAsync(
            DeviceCredentials credentials,
            ActivityStateSnapshot snapshot,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        ArgumentNullException.ThrowIfNull(
            snapshot
        );

        int idleSeconds =
            checked(
                (int)Math.Min(
                    snapshot.IdleSeconds,
                    86_400L
                )
            );

        ActivityStateRequest request =
            new()
            {
                State =
                    snapshot.State,

                IdleSeconds =
                    idleSeconds,

                LastInputAt =
                    snapshot.LastInputAt,

                ObservedAt =
                    snapshot.ObservedAt
            };

        ActivityStateResponse response =
            await _apiClient
                .ReportStateAsync(
                    credentials,
                    request,
                    cancellationToken
                );

        bool stateChanged =
            _lastReportedSnapshot is null
            || !string.Equals(
                _lastReportedSnapshot.State,
                snapshot.State,
                StringComparison.Ordinal
            );

        _lastReportedSnapshot =
            snapshot;

        if (
            stateChanged
        )
        {
            _logger.LogInformation(
                "WorkforceOS activity state changed to {ActivityState}. Idle seconds: {IdleSeconds}.",
                response.State,
                response.IdleSeconds
            );
        }
        else
        {
            _logger.LogDebug(
                "WorkforceOS activity state reported as {ActivityState}. Idle seconds: {IdleSeconds}.",
                response.State,
                response.IdleSeconds
            );
        }

        return response;
    }

    public bool ShouldReport(
        ActivityStateSnapshot snapshot,
        DateTimeOffset? lastReportAt
    )
    {
        ArgumentNullException.ThrowIfNull(
            snapshot
        );

        if (
            _lastReportedSnapshot is null
        )
        {
            return true;
        }

        if (
            !string.Equals(
                _lastReportedSnapshot.State,
                snapshot.State,
                StringComparison.Ordinal
            )
        )
        {
            return true;
        }

        if (
            lastReportAt is null
        )
        {
            return true;
        }

        TimeSpan elapsed =
            snapshot.ObservedAt
            - lastReportAt.Value;

        return (
            elapsed.TotalSeconds
            >= _options.ReportIntervalSeconds
        );
    }
}