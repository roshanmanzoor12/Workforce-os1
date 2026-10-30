using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Configuration;
using Microsoft.Extensions.Options;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Read-only request discovery. Never starts video capture or approves consent.
/// </summary>
public sealed class LiveScreenInboxWorker : BackgroundService
{
    private readonly EnrollmentService _enrollment;
    private readonly LiveScreenInboxClient _client;
    private readonly ILogger<LiveScreenInboxWorker> _logger;
    private readonly AgentOptions _options;

    public LiveScreenInboxWorker(
        EnrollmentService enrollment,
        LiveScreenInboxClient client,
        ILogger<LiveScreenInboxWorker> logger,
        IOptions<AgentOptions> options)
    {
        _enrollment = enrollment;
        _client = client;
        _logger = logger;
        _options = options.Value;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var tracker = new LiveScreenInboxStateTracker();
        var handled = new HashSet<Guid>();
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var credentials = await _enrollment.GetCredentialsAsync(stoppingToken);
                if (credentials is not null && credentials.IsValid())
                {
                    var inbox = await _client.ReadAsync(credentials, stoppingToken);
                    var valid = inbox.Sessions
                        .Where(s => s.ExpiresAt > DateTimeOffset.UtcNow &&
                            (s.Status == "requested" || s.Status == "accepted" || s.Status == "active"))
                        .ToList();
                    _logger.LogInformation("Live-screen inbox poll: sessions={Count} consent={Consent} authorized={Authorized}", valid.Count, inbox.ConsentGranted, inbox.CaptureAuthorized);
                    var liveIds = valid.Select(s => s.SessionId).ToHashSet();
                    handled.IntersectWith(liveIds);

                    foreach (var item in valid)
                    {
                        if (handled.Contains(item.SessionId)) continue;
                        if (item.Status == "requested")
                        {
                            // Never turn generic monitoring disclosure into a
                            // screen-sharing decision. A saved screen-specific
                            // grant must be checked with Companion proof first.
                            var decision = await CompanionRequestNotifier.RequestDecisionAsync(
                                item.SessionId, item.ExpiresAt, stoppingToken);
                            if (decision is "accept" or "decline")
                            {
                                var accepted = decision == "accept";
                                var status = await _client.DecideAsync(credentials, item.SessionId, accepted, stoppingToken);
                                if (!accepted || status != "accepted")
                                {
                                    handled.Add(item.SessionId);
                                    _logger.LogInformation("Live-screen session {SessionId} employee decision: {Status}.", item.SessionId, status);
                                    continue;
                                }
                                var activatedStatus = await _client.ActivateAsync(credentials, item.SessionId, stoppingToken);
                                if (activatedStatus != "active")
                                {
                                    _logger.LogWarning("Live-screen activation pending for {SessionId}: {Status}", item.SessionId, activatedStatus);
                                    continue;
                                }
                            }
                            else continue;
                        }
                        else if (item.Status == "accepted")
                        {
                            // Employee has already accepted. Retry activation, never fabricate approval.
                            var activatedStatus = await _client.ActivateAsync(credentials, item.SessionId, stoppingToken);
                            if (activatedStatus != "active")
                            {
                                _logger.LogWarning("Live-screen activation retry pending for {SessionId}: {Status}", item.SessionId, activatedStatus);
                                continue;
                            }
                        }

                        // Recovery path: an active session can outlive an agent or
                        // companion restart. Re-send its authenticated start command.
                        var started = await CompanionRequestNotifier.StartCaptureAsync(
                            item.SessionId, _options.ApiBaseUrl, credentials, stoppingToken);
                        if (started)
                        {
                            handled.Add(item.SessionId);
                            _logger.LogInformation("Live-screen session {SessionId} capture start sent (status {Status}).", item.SessionId, item.Status);
                        }
                    }

                    var change = tracker.Observe(inbox, DateTimeOffset.UtcNow);
                    if (change.Changed)
                        _logger.LogInformation("Live-screen inbox connected: {Count} valid request(s), {Added} new, {Removed} removed.", change.CurrentCount, change.AddedCount, change.RemovedCount);
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { break; }
            catch (Exception ex)
            {
                if (tracker.MarkUnavailable()) _logger.LogWarning("Live-screen inbox unavailable ({ErrorType}); retrying.", ex.GetType().Name);
            }
            try { await Task.Delay(TimeSpan.FromSeconds(15), stoppingToken); }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested) { break; }
        }
    }

}


