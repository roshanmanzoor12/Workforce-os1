#!/usr/bin/env python3
"""Install device-authenticated, read-only live-session inbox polling into WorkforceOS Agent.
Does not capture screens, activate sessions, or transmit media.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys

CLIENT = r'''using System.Net.Http.Json;
using System.Text.Json.Serialization;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.LiveScreen;

public sealed record LiveScreenInboxItem
{
    [JsonPropertyName("session_id")]
    public Guid SessionId { get; init; }

    [JsonPropertyName("status")]
    public string Status { get; init; } = "";

    [JsonPropertyName("expires_at")]
    public DateTimeOffset ExpiresAt { get; init; }

    [JsonPropertyName("consent_required")]
    public bool ConsentRequired { get; init; }

    [JsonPropertyName("visible_indicator_required")]
    public bool VisibleIndicatorRequired { get; init; }
}

public sealed record LiveScreenInboxResponse
{
    [JsonPropertyName("sessions")]
    public List<LiveScreenInboxItem> Sessions { get; init; } = new();

    [JsonPropertyName("capture_authorized")]
    public bool CaptureAuthorized { get; init; }
}

public sealed class LiveScreenInboxClient
{
    private const string InboxPath = "/api/v1/device-agent/live-screen/inbox";
    private readonly IHttpClientFactory _httpClientFactory;

    public LiveScreenInboxClient(IHttpClientFactory httpClientFactory)
    {
        _httpClientFactory = httpClientFactory;
    }

    public async Task<LiveScreenInboxResponse> ReadAsync(
        DeviceCredentials credentials,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(credentials);
        if (!credentials.IsValid())
            throw new ArgumentException("Invalid device credentials.", nameof(credentials));

        using var client = _httpClientFactory.CreateClient(WorkforceApiClient.HttpClientName);
        using var request = new HttpRequestMessage(HttpMethod.Get, InboxPath);
        request.Headers.TryAddWithoutValidation("X-Device-UUID", credentials.DeviceUuid.ToString("D"));
        request.Headers.TryAddWithoutValidation("X-Device-Secret", credentials.DeviceSecret);
        using var response = await client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
        response.EnsureSuccessStatusCode();
        var inbox = await response.Content.ReadFromJsonAsync<LiveScreenInboxResponse>(cancellationToken);
        if (inbox is null || !IsValid(inbox))
            throw new InvalidDataException("Live-screen inbox returned invalid data.");
        return inbox;
    }

    // Strict shape validation; inbox is informational, not a capture lease.
    public static bool IsValid(LiveScreenInboxResponse? inbox)
    {
        if (inbox is null || inbox.Sessions is null || inbox.Sessions.Count > 20)
            return false;
        foreach (var item in inbox.Sessions)
        {
            if (item is null || item.SessionId == Guid.Empty ||
                item.ExpiresAt == default ||
                (item.Status != "requested" && item.Status != "accepted"))
                return false;
        }
        return true;
    }
}
'''

WORKER = r'''using Microsoft.Extensions.Hosting;
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
        while (!stoppingToken.IsCancellationRequested)
        {
            try
            {
                var credentials = await _enrollment.GetCredentialsAsync(stoppingToken);
                if (credentials is not null && credentials.IsValid())
                {
                    var inbox = await _client.ReadAsync(credentials, stoppingToken);
                    // Read-only visibility: no session activation and no capture.
                    if (inbox.Sessions.Count > 0)
                    {
                        _logger.LogInformation(
                            "Live-screen inbox contains {Count} request(s); capture is not enabled by inbox responses.",
                            inbox.Sessions.Count);
                    }
                }
            }
            catch (OperationCanceledException) when (stoppingToken.IsCancellationRequested)
            {
                break;
            }
            catch (Exception ex)
            {
                // Never log credentials or response payloads.
                _logger.LogWarning("Live-screen inbox unavailable ({ErrorType}); retrying.",
                    ex.GetType().Name);
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
'''

TEST = r'''using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenInboxValidationTests
{
    [Fact]
    public void EmptyInboxIsValid()
    {
        Assert.True(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse()));
    }

    [Fact]
    public void NullInboxIsInvalid()
    {
        Assert.False(LiveScreenInboxClient.IsValid(null));
    }

    [Fact]
    public void MissingSessionIdentityIsInvalid()
    {
        Assert.False(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.Empty, Status = "requested",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1)
            }}
        }));
    }

    [Fact]
    public void InvalidStatusIsRejected()
    {
        Assert.False(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.NewGuid(), Status = "active",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1)
            }}
        }));
    }

    [Fact]
    public void RequestedSessionIsAcceptedForReadOnlyDiscovery()
    {
        Assert.True(LiveScreenInboxClient.IsValid(new LiveScreenInboxResponse
        {
            CaptureAuthorized = false,
            Sessions = new List<LiveScreenInboxItem> { new()
            {
                SessionId = Guid.NewGuid(), Status = "requested",
                ExpiresAt = DateTimeOffset.UtcNow.AddMinutes(1),
                ConsentRequired = true, VisibleIndicatorRequired = true
            }}
        }));
    }
}
'''

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
    program=root/'agent/WorkforceOS.Agent/program.cs'
    if not program.exists(): raise SystemExit(f'Missing {program}')
    src=program.read_text(encoding='utf-8-sig')
    if 'LiveScreenInboxWorker' in src:
        print('ALREADY INSTALLED - no changes'); return
    anchor='        // AGENT CONFIGURATION'
    if anchor not in src or 'builder.Services.AddHttpClient(' not in src:
        raise SystemExit('Unexpected program.cs structure; nothing changed')
    files={
      root/'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxClient.cs':CLIENT,
      root/'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxWorker.cs':WORKER,
      root/'agent/WorkforceOS.Agent.Tests/LiveScreen/LiveScreenInboxValidationTests.cs':TEST,
    }
    for p in files:
        if p.exists(): raise SystemExit(f'Refusing to overwrite existing file: {p}')
    updated=src.replace(anchor,'''        // READ-ONLY DEVICE LIVE-SESSION DISCOVERY
        // Does not authorize or start screen capture.
        builder.Services.AddSingleton<WorkforceOS.Agent.LiveScreen.LiveScreenInboxClient>();
        builder.Services.AddHostedService<WorkforceOS.Agent.LiveScreen.LiveScreenInboxWorker>();

'''+anchor,1)
    backup=root/'backups'/('agent-inbox-runtime-'+datetime.now().strftime('%Y%m%d-%H%M%S'))/'agent/WorkforceOS.Agent/program.cs'
    backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(program,backup)
    try:
        for path,content in files.items():
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        program.write_text(updated,encoding='utf-8')
    except Exception:
        shutil.copy2(backup,program)
        for p in files: p.unlink(missing_ok=True)
        raise
    print('PATCHED',program)
    for p in files: print('ADDED',p)
    print('BACKUP',backup)
    print('NOTE: Agent now polls device-authenticated inbox; still NO capture, consent lease, or WebRTC.')

if __name__=='__main__': main()
