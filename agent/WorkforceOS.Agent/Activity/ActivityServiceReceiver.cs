using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityServiceReceiver :
    BackgroundService
{
    private static readonly TimeSpan
        FailureDelay =
            TimeSpan.FromSeconds(
                2
            );

    private readonly ActivityPipeServer
        _pipeServer;

    private readonly ActivityRuntimeState
        _runtimeState;

    private readonly ILogger<ActivityServiceReceiver>
        _logger;

    public ActivityServiceReceiver(
        ActivityPipeServer pipeServer,
        ActivityRuntimeState runtimeState,
        ILogger<ActivityServiceReceiver> logger
    )
    {
        _pipeServer =
            pipeServer;

        _runtimeState =
            runtimeState;

        _logger =
            logger;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken
    )
    {
        _logger.LogInformation(
            "WorkforceOS activity IPC receiver started."
        );

        while (
            !stoppingToken
                .IsCancellationRequested
        )
        {
            try
            {
                ActivitySessionObservation observation =
                    await _pipeServer
                        .ReceiveAsync(
                            stoppingToken
                        );

                _runtimeState.RecordObservation(
                    observation
                );

                _logger.LogDebug(
                    "Activity observation received. Session={SessionId}, State={State}, IdleSeconds={IdleSeconds}.",
                    observation.SessionId,
                    observation.State,
                    observation.IdleSeconds
                );
            }
            catch (
                OperationCanceledException
            )
            when (
                stoppingToken
                    .IsCancellationRequested
            )
            {
                break;
            }
            catch (
                UnauthorizedAccessException exception
            )
            {
                _runtimeState.RecordError(
                    exception
                );

                _logger.LogWarning(
                    exception,
                    "Rejected unauthorized WorkforceOS activity IPC client."
                );

                await DelayAfterFailureAsync(
                    stoppingToken
                );
            }
            catch (
                Exception exception
            )
            {
                _runtimeState.RecordError(
                    exception
                );

                _logger.LogError(
                    exception,
                    "WorkforceOS activity IPC receiver failed while processing an observation."
                );

                await DelayAfterFailureAsync(
                    stoppingToken
                );
            }
        }

        _logger.LogInformation(
            "WorkforceOS activity IPC receiver stopped."
        );
    }

    private static async Task
        DelayAfterFailureAsync(
            CancellationToken stoppingToken
        )
    {
        try
        {
            await Task.Delay(
                FailureDelay,
                stoppingToken
            );
        }
        catch (
            OperationCanceledException
        )
        when (
            stoppingToken
                .IsCancellationRequested
        )
        {
            // Normal service shutdown.
        }
    }
}