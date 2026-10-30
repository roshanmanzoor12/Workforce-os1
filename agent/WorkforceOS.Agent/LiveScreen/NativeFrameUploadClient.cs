using System.Net;
using System.Net.Http.Headers;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Authenticated device-side JPEG upload transport. This class does NOT capture a
/// screen, grant consent or accept arbitrary network requests. A separate,
/// authenticated and employee-approved local IPC bridge must supply each frame.
/// Never place DeviceCredentials in the interactive Screen Companion.
/// </summary>
public sealed class NativeFrameUploadClient
{
    private const int MaxFrameBytes = 900_000;
    private readonly IHttpClientFactory _httpClientFactory;

    public NativeFrameUploadClient(IHttpClientFactory httpClientFactory) =>
        _httpClientFactory = httpClientFactory;

    public async Task<bool> UploadApprovedFrameAsync(
        DeviceCredentials credentials,
        Guid sessionId,
        ReadOnlyMemory<byte> jpeg,
        bool employeeApprovedAndVisible,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(credentials);
        if (!credentials.IsValid() || sessionId == Guid.Empty || !employeeApprovedAndVisible)
            return false;
        if (!IsBoundedJpeg(jpeg.Span)) return false;

        using var client = _httpClientFactory.CreateClient(WorkforceApiClient.HttpClientName);
        using var request = new HttpRequestMessage(
            HttpMethod.Post,
            $"/api/v1/device-agent/live-screen/{sessionId:D}/native-frame");
        request.Headers.TryAddWithoutValidation("X-Device-UUID", credentials.DeviceUuid.ToString("D"));
        request.Headers.TryAddWithoutValidation("X-Device-Secret", credentials.DeviceSecret);
        request.Content = new ByteArrayContent(jpeg.ToArray());
        request.Content.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
        using var response = await client.SendAsync(request, cancellationToken);
        // 403/404/410 means the authorization or session is no longer valid.
        // Callers MUST stop transmitting rather than retrying rejected frames.
        if (response.StatusCode is HttpStatusCode.Forbidden or HttpStatusCode.NotFound or HttpStatusCode.Gone)
            return false;
        response.EnsureSuccessStatusCode();
        return response.IsSuccessStatusCode;
    }

    public static bool IsBoundedJpeg(ReadOnlySpan<byte> data) =>
        data.Length >= 4 && data.Length <= MaxFrameBytes &&
        data[0] == 0xFF && data[1] == 0xD8 &&
        data[^2] == 0xFF && data[^1] == 0xD9;
}
