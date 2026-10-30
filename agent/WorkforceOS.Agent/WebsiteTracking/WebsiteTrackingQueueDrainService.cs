namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingQueueDrainService
{
    private readonly
        WebsiteTrackingObservationQueue
        _queue;

    private readonly
        WebsiteTrackingBackendReporter
        _reporter;

    public WebsiteTrackingQueueDrainService(
        WebsiteTrackingObservationQueue
            queue,
        WebsiteTrackingBackendReporter
            reporter
    )
    {
        _queue =
            queue;

        _reporter =
            reporter;
    }

    public async Task<
        WebsiteTrackingReportResult
    > DrainOneAsync(
        CancellationToken cancellationToken
    )
    {
        WebsiteTrackingObservation
            observation =
                await _queue.ReadAsync(
                    cancellationToken
                );

        return await _reporter.ReportAsync(
            observation,
            cancellationToken
        );
    }
}