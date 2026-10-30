using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingBackendReportingWorker
    : BackgroundService
{
    private readonly AppTrackingBackendReporter _reporter;

    private readonly DeviceCredentialStore _credentialStore;

    private readonly AppTrackingOptions _options;

    private readonly ILogger<AppTrackingBackendReportingWorker> _logger;

    public AppTrackingBackendReportingWorker(
        AppTrackingBackendReporter reporter,
        DeviceCredentialStore credentialStore,
        AppTrackingOptions options,
        ILogger<AppTrackingBackendReportingWorker> logger)
    {
        _reporter = reporter;
        _credentialStore = credentialStore;
        _options = options;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken)
    {
        if (!_options.Enabled)
        {
            _logger.LogInformation(
                "WorkforceOS App Tracking backend reporter is disabled.");

            return;
        }

        _options.Validate();

        TimeSpan interval =
            TimeSpan.FromSeconds(
                Math.Max(
                    5,
                    _options.ReportIntervalSeconds));

        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                DeviceCredentials? credentials =
                    await _credentialStore.LoadAsync(
                        stoppingToken);

                if (credentials is not null)
                {
                    await _reporter.ReportLatestAsync(
                        credentials.DeviceUuid,
                        credentials.DeviceSecret,
                        stoppingToken);
                }
            }
            catch (OperationCanceledException)
                when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception exception)
            {
                _logger.LogError(
                    exception,
                    "WorkforceOS App Tracking backend reporting failed.");
            }

            try
            {
                await Task.Delay(
                    interval,
                    stoppingToken);
            }
            catch (OperationCanceledException)
                when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
        }
    }
}