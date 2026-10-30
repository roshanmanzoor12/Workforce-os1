using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivitySessionHelperRunner
{
    private static readonly TimeSpan
        PipeConnectionTimeout =
            TimeSpan.FromSeconds(
                5
            );

    private readonly LastInputDetector
        _lastInputDetector;

    private readonly ActivityPipeClient
        _pipeClient;

    private readonly ActivityOptions
        _options;

    private readonly ILogger<ActivitySessionHelperRunner>
        _logger;

    public ActivitySessionHelperRunner(
        LastInputDetector lastInputDetector,
        ActivityPipeClient pipeClient,
        IOptions<ActivityOptions> options,
        ILogger<ActivitySessionHelperRunner> logger
    )
    {
        _lastInputDetector =
            lastInputDetector;

        _pipeClient =
            pipeClient;

        _options =
            options.Value;

        _logger =
            logger;
    }

    public async Task RunAsync(
        CancellationToken cancellationToken = default
    )
    {
        if (
            !_options.Enabled
        )
        {
            _logger.LogInformation(
                "WorkforceOS activity monitoring is disabled."
            );

            return;
        }

        ValidateOptions();

        ActivitySessionIdentity identity =
            ActivitySessionIdentity.Current();

        if (
            identity.SessionId
            <= 0
        )
        {
            throw new InvalidOperationException(
                "Activity session helper must run inside an interactive Windows user session."
            );
        }

        ActivityStateTracker tracker =
            new(
                _options.IdleThresholdSeconds
            );

        string? lastSentState =
            null;

        DateTimeOffset?
            lastSentAt =
                null;

        _logger.LogInformation(
            "WorkforceOS disclosed activity session helper started. Session={SessionId}.",
            identity.SessionId
        );

        while (
            !cancellationToken
                .IsCancellationRequested
        )
        {
            try
            {
                LastInputSnapshot inputSnapshot =
                    _lastInputDetector
                        .GetSnapshot();

                ActivityStateSnapshot stateSnapshot =
                    tracker.Evaluate(
                        inputSnapshot
                    );

                bool stateChanged =
                    !string.Equals(
                        lastSentState,
                        stateSnapshot.State,
                        StringComparison.Ordinal
                    );

                bool periodicReportDue =
                    lastSentAt is null
                    ||
                    (
                        stateSnapshot.ObservedAt
                        - lastSentAt.Value
                    ).TotalSeconds
                    >= _options.ReportIntervalSeconds;

                if (
                    stateChanged
                    ||
                    periodicReportDue
                )
                {
                    ActivitySessionObservation observation =
                        new()
                        {
                            SessionId =
                                identity.SessionId,

                            UserSid =
                                identity.UserSid,

                            State =
                                stateSnapshot.State,

                            IdleSeconds =
                                stateSnapshot.IdleSeconds,

                            LastInputAt =
                                stateSnapshot.LastInputAt,

                            ObservedAt =
                                stateSnapshot.ObservedAt
                        };

                    await _pipeClient
                        .SendAsync(
                            observation,
                            PipeConnectionTimeout,
                            cancellationToken
                        );

                    lastSentState =
                        stateSnapshot.State;

                    lastSentAt =
                        stateSnapshot.ObservedAt;
                }
            }
            catch (
                OperationCanceledException
            )
            when (
                cancellationToken
                    .IsCancellationRequested
            )
            {
                break;
            }
            catch (
                TimeoutException exception
            )
            {
                _logger.LogWarning(
                    exception,
                    "WorkforceOS activity service pipe is temporarily unavailable."
                );
            }
            catch (
                Exception exception
            )
            {
                _logger.LogError(
                    exception,
                    "WorkforceOS activity session helper observation failed."
                );
            }

            try
            {
                await Task.Delay(
                    TimeSpan.FromSeconds(
                        _options
                            .ObservationIntervalSeconds
                    ),
                    cancellationToken
                );
            }
            catch (
                OperationCanceledException
            )
            when (
                cancellationToken
                    .IsCancellationRequested
            )
            {
                break;
            }
        }

        _logger.LogInformation(
            "WorkforceOS activity session helper stopped."
        );
    }

    private void ValidateOptions()
    {
        if (
            _options.IdleThresholdSeconds
            < 5
        )
        {
            throw new InvalidOperationException(
                "Activity idle threshold must be at least 5 seconds."
            );
        }

        if (
            _options.ObservationIntervalSeconds
            < 1
            ||
            _options.ObservationIntervalSeconds
            > 300
        )
        {
            throw new InvalidOperationException(
                "Activity observation interval must be between 1 and 300 seconds."
            );
        }

        if (
            _options.ReportIntervalSeconds
            < _options.ObservationIntervalSeconds
            ||
            _options.ReportIntervalSeconds
            > 3600
        )
        {
            throw new InvalidOperationException(
                "Activity report interval must be at least the observation interval and no more than 3600 seconds."
            );
        }
    }
}