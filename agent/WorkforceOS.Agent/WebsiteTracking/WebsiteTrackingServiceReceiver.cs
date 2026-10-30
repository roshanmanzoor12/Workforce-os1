using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingServiceReceiver
    : BackgroundService
{
    private readonly
        WebsiteTrackingPipeServer
        _pipeServer;

    private readonly
        WebsiteTrackingOptions
        _options;

    private readonly
        ILogger<
            WebsiteTrackingServiceReceiver
        >
        _logger;

    public WebsiteTrackingServiceReceiver(
        WebsiteTrackingPipeServer pipeServer,
        IOptions<
            WebsiteTrackingOptions
        > options,
        ILogger<
            WebsiteTrackingServiceReceiver
        > logger
    )
    {
        _pipeServer =
            pipeServer;

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
                "Website Tracking service receiver is disabled."
            );

            return;
        }

        _logger.LogInformation(
            "Website Tracking persistent pipe receiver started."
        );

        try
        {
            await _pipeServer.RunAsync(
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
        }

        _logger.LogInformation(
            "Website Tracking persistent pipe receiver stopped."
        );
    }
}