using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Activity;

public sealed class ActivityBackendReportingWorker :
    BackgroundService
{
    private static readonly TimeSpan
        MissingCredentialDelay =
            TimeSpan.FromSeconds(
                15
            );

    private static readonly TimeSpan
        FailureDelay =
            TimeSpan.FromSeconds(
                10
            );

    private readonly ActivityBackendReporter
        _backendReporter;

    private readonly DeviceCredentialStore
        _credentialStore;

    private readonly ActivityOptions
        _options;

    private readonly ILogger<ActivityBackendReportingWorker>
        _logger;

    public ActivityBackendReportingWorker(
        ActivityBackendReporter backendReporter,
        DeviceCredentialStore credentialStore,
        IOptions<ActivityOptions> options,
        ILogger<ActivityBackendReportingWorker> logger
    )
    {
        _backendReporter =
            backendReporter;

        _credentialStore =
            credentialStore;

        _options =
            options.Value;

        _logger =
            logger;
    }

    protected override async Task ExecuteAsync(
        CancellationToken stoppingToken
    )
    {
        if (
            !_options.Enabled
        )
        {
            _logger.LogInformation(
                "WorkforceOS activity backend reporting is disabled."
            );

            return;
        }

        _logger.LogInformation(
            "WorkforceOS activity backend reporting worker started."
        );

        while (
            !stoppingToken
                .IsCancellationRequested
        )
        {
            try
            {
                DeviceCredentials? credentials =
                    await _credentialStore
                        .LoadAsync(
                            stoppingToken
                        );

                if (
                    credentials is null
                    ||
                    !credentials.IsValid()
                )
                {
                    await DelayAsync(
                        MissingCredentialDelay,
                        stoppingToken
                    );

                    continue;
                }

                await _backendReporter
                    .TryReportLatestAsync(
                        credentials,
                        stoppingToken
                    );

                await DelayAsync(
                    TimeSpan.FromSeconds(
                        Math.Max(
                            5,
                            _options
                                .ObservationIntervalSeconds
                        )
                    ),
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
                break;
            }
            catch (
                Exception exception
            )
            {
                _logger.LogWarning(
                    exception,
                    "WorkforceOS activity backend reporting iteration failed."
                );

                await DelayAsync(
                    FailureDelay,
                    stoppingToken
                );
            }
        }

        _logger.LogInformation(
            "WorkforceOS activity backend reporting worker stopped."
        );
    }

    private static async Task DelayAsync(
        TimeSpan delay,
        CancellationToken cancellationToken
    )
    {
        try
        {
            await Task.Delay(
                delay,
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
            // Normal shutdown.
        }
    }
}