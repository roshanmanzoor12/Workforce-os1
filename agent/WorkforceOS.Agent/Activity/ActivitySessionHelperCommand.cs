using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivitySessionHelperCommand
{
    private readonly ActivitySessionHelperRunner
        _runner;

    private readonly ILogger<ActivitySessionHelperCommand>
        _logger;

    public ActivitySessionHelperCommand(
        ActivitySessionHelperRunner runner,
        ILogger<ActivitySessionHelperCommand> logger
    )
    {
        _runner =
            runner;

        _logger =
            logger;
    }

    public async Task<int> RunAsync(
        CancellationToken cancellationToken = default
    )
    {
        try
        {
            ActivitySessionIdentity identity =
                ActivitySessionIdentity
                    .Current();

            if (
                identity.SessionId
                <= 0
            )
            {
                _logger.LogError(
                    "Activity session helper cannot run in Windows Session 0."
                );

                return 2;
            }

            _logger.LogInformation(
                "Starting WorkforceOS disclosed activity helper in Windows session {SessionId}.",
                identity.SessionId
            );

            await _runner.RunAsync(
                cancellationToken
            );

            return 0;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            return 0;
        }
        catch (
            Exception exception
        )
        {
            _logger.LogError(
                exception,
                "WorkforceOS activity session helper failed."
            );

            return 1;
        }
    }
}