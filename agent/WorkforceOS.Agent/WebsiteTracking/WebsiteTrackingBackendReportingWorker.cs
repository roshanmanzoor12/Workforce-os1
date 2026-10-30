using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class
    WebsiteTrackingBackendReportingWorker
    : BackgroundService
{
    private readonly
        WebsiteTrackingObservationQueue
        _queue;

    private readonly
        WebsiteTrackingBackendReporter
        _reporter;

    private readonly
        WebsiteTrackingOptions
        _options;

    private readonly
        ILogger<
            WebsiteTrackingBackendReportingWorker
        >
        _logger;

    public WebsiteTrackingBackendReportingWorker(
        WebsiteTrackingObservationQueue queue,
        WebsiteTrackingBackendReporter reporter,
        IOptions<
            WebsiteTrackingOptions
        > options,
        ILogger<
            WebsiteTrackingBackendReportingWorker
        > logger
    )
    {
        _queue =
            queue;

        _reporter =
            reporter;

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
                "Website Tracking backend reporting is disabled."
            );

            return;
        }

        _logger.LogInformation(
            "Website Tracking backend reporting worker started."
        );

        await foreach (
            WebsiteTrackingObservation observation
            in _queue.ReadAllAsync(
                stoppingToken
            )
        )
        {
            try
            {
                WebsiteTrackingReportResult result =
                    await _reporter.ReportAsync(
                        observation,
                        stoppingToken
                    );

                if (
                    result.IsSuccess
                )
                {
                    continue;
                }

                _logger.LogWarning(
                    "Website Tracking observation report failed with status {Status}.",
                    result.Status
                );

                await Task.Delay(
                    TimeSpan.FromSeconds(
                        Math.Max(
                            1,
                            _options
                                .ReportIntervalSeconds
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
                    "Unhandled Website Tracking reporting worker error."
                );

                try
                {
                    await Task.Delay(
                        TimeSpan.FromSeconds(
                            5
                        ),
                        stoppingToken
                    );
                }
                catch (
                    OperationCanceledException
                )
                {
                    break;
                }
            }
        }

        _logger.LogInformation(
            "Website Tracking backend reporting worker stopped."
        );
    }
}