namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingSessionHelperCommand
{
    private readonly AppTrackingSessionHelperRunner _runner;

    private readonly ILogger<AppTrackingSessionHelperCommand> _logger;

    public AppTrackingSessionHelperCommand(
        AppTrackingSessionHelperRunner runner,
        ILogger<AppTrackingSessionHelperCommand> logger)
    {
        _runner = runner;
        _logger = logger;
    }

    public async Task<int> RunAsync(
        CancellationToken cancellationToken)
    {
        try
        {
            await _runner.RunAsync(
                cancellationToken);

            return 0;
        }
        catch (OperationCanceledException)
            when (cancellationToken.IsCancellationRequested)
        {
            return 0;
        }
        catch (Exception exception)
        {
            _logger.LogError(
                exception,
                "WorkforceOS App Tracking helper failed.");

            return 1;
        }
    }
}