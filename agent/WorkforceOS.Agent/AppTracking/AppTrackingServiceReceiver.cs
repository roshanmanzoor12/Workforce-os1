namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingServiceReceiver
    : BackgroundService
{
    private readonly AppTrackingPipeServer _pipeServer;

    private readonly AppTrackingRuntimeCoordinator _coordinator;

    private readonly AppTrackingRuntimeState _runtimeState;

    private readonly AppTrackingOptions _options;

    private readonly ILogger<AppTrackingServiceReceiver> _logger;

    public AppTrackingServiceReceiver(
        AppTrackingPipeServer pipeServer,
        AppTrackingRuntimeCoordinator coordinator,
        AppTrackingRuntimeState runtimeState,
        AppTrackingOptions options,
        ILogger<AppTrackingServiceReceiver> logger)
    {
        _pipeServer =
            pipeServer;

        _coordinator =
            coordinator;

        _runtimeState =
            runtimeState;

        _options =
            options;

        _logger =
            logger;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken)
    {
        if (!_options.Enabled)
        {
            _logger.LogInformation(
                "WorkforceOS App Tracking receiver is disabled.");

            return;
        }

        _options.Validate();

        _logger.LogInformation(
            "WorkforceOS disclosed App Tracking receiver started.");

        while (
            !stoppingToken.IsCancellationRequested)
        {
            try
            {
                AppTrackingSessionObservation observation =
                    await _pipeServer.ReceiveAsync(
                        stoppingToken);

                _coordinator.Process(
                    observation);
            }
            catch (OperationCanceledException)
                when (
                    stoppingToken
                        .IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _runtimeState.RecordError(
                    exception);

                _logger.LogError(
                    exception,
                    "WorkforceOS App Tracking receiver failed.");

                try
                {
                    await Task.Delay(
                        TimeSpan.FromSeconds(
                            2),
                        stoppingToken);
                }
                catch (OperationCanceledException)
                    when (
                        stoppingToken
                            .IsCancellationRequested)
                {
                    break;
                }
            }
        }

        _logger.LogInformation(
            "WorkforceOS App Tracking receiver stopped.");
    }
}