using System.Net.Http.Json;
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

    [JsonPropertyName("consent_granted")]
    public bool ConsentGranted { get; init; }
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

    public async Task<string> DecideAsync(
        DeviceCredentials credentials, Guid sessionId, bool accepted,
        CancellationToken cancellationToken = default)
    {
        using var client = _httpClientFactory.CreateClient(WorkforceApiClient.HttpClientName);
        using var request = new HttpRequestMessage(HttpMethod.Post, $"/api/v1/device-agent/live-screen/{sessionId:D}/decision");
        request.Headers.TryAddWithoutValidation("X-Device-UUID", credentials.DeviceUuid.ToString("D"));
        request.Headers.TryAddWithoutValidation("X-Device-Secret", credentials.DeviceSecret);
        request.Content = JsonContent.Create(new { accepted, visible_indicator_shown = accepted });
        using var response = await client.SendAsync(request, cancellationToken);
        response.EnsureSuccessStatusCode();
        var body = await response.Content.ReadFromJsonAsync<Dictionary<string,string>>(cancellationToken);
        return body?.GetValueOrDefault("status") ?? "unknown";
    }

    public async Task<string> ActivateAsync(
        DeviceCredentials credentials, Guid sessionId,
        CancellationToken cancellationToken = default)
    {
        using var client = _httpClientFactory.CreateClient(WorkforceApiClient.HttpClientName);
        using var request = new HttpRequestMessage(HttpMethod.Post, $"/api/v1/device-agent/live-screen/{sessionId:D}/activate");
        request.Headers.TryAddWithoutValidation("X-Device-UUID", credentials.DeviceUuid.ToString("D"));
        request.Headers.TryAddWithoutValidation("X-Device-Secret", credentials.DeviceSecret);
        using var response = await client.SendAsync(request, cancellationToken);
        response.EnsureSuccessStatusCode();
        var body = await response.Content.ReadFromJsonAsync<Dictionary<string,string>>(cancellationToken);
        return body?.GetValueOrDefault("status") ?? "unknown";
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
                (item.Status != "requested" && item.Status != "accepted" && item.Status != "active"))
                return false;
        }
        return true;
    }
}


