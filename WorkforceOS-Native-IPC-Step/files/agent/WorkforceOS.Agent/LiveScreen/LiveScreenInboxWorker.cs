using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Enrollment;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Read-only request discovery. Never starts video capture or approves consent.
/// </summary>
public sealed class LiveScreenInboxWorker : BackgroundService
{
    private readonly EnrollmentService _enrollment;
    private readonly LiveScreenInboxClient _client;
    private readonly ILogger<LiveScreenInboxWorker> _logger;

    public LiveScreenInboxWorker(
        EnrollmentService enrollment,
        LiveScreenInboxClient client,
        ILogger<LiveScreenInboxWorker> logger)
    {
        _enrollment = enrollment;
        _client = client;
        _logger = logger;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var tracker = new LiveScreenInboxStateTracker();
        var notified = new HashSet<Guid>();
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var credentials = await _enrollment.GetCredentialsAsync(stoppingToken);
                if (credentials is not null && credentials.IsValid())
                {
                    var inbox = await _client.ReadAsync(credentials, stoppingToken);
                    // Read-only visibility: never activate/capture from inbox data.
                    // Only send informational popups for newly observed requested sessions.
                    // Never interpret inbox as authority to start capture.
                    var currentlyRequested = inbox.Sessions
                        .Where(s => s.Status == "requested" && s.ExpiresAt > DateTimeOffset.UtcNow)
                        .Select(s => s.SessionId).ToHashSet();
                    notified.IntersectWith(currentlyRequested);
                    foreach (var pending in inbox.Sessions.Where(s => currentlyRequested.Contains(s.SessionId)))
                    {
                        if (!notified.Contains(pending.SessionId) &&
                            await CompanionRequestNotifier.TryNotifyAsync(pending.SessionId, pending.ExpiresAt, stoppingToken))
                            notified.Add(pending.SessionId);
                    }
                    var change = tracker.Observe(inbox, DateTimeOffset.UtcNow);
                    if (change.Changed)
                    {
                        _logger.LogInformation(
                            "Live-screen inbox connected: {Count} valid request(s), {Added} new, {Removed} removed. Media transport not configured.",
                            change.CurrentCount, change.AddedCount, change.RemovedCount);
                    }
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                // Do not log credentials, response payloads, or repeated outages.
                if (tracker.MarkUnavailable())
                    _logger.LogWarning("Live-screen inbox unavailable ({ErrorType}); retrying.", ex.GetType().Name);
            }
            try
            {
                await Task.Delay(TimeSpan.FromSeconds(15), stoppingToken);
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
        }
    }
}
