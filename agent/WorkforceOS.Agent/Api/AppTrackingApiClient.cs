using System.Net.Http.Json;
using WorkforceOS.Agent.Configuration;

namespace WorkforceOS.Agent.Api;

public sealed class AppTrackingApiClient
{
    private const string DeviceUuidHeader =
        "X-Device-UUID";

    private const string DeviceSecretHeader =
        "X-Device-Secret";

    private const string ObservationPath =
        "/api/v1/device-agent/app-observation";

    private readonly IHttpClientFactory _httpClientFactory;

    private readonly ILogger<AppTrackingApiClient> _logger;

    public AppTrackingApiClient(
        IHttpClientFactory httpClientFactory,
        ILogger<AppTrackingApiClient> logger)
    {
        _httpClientFactory =
            httpClientFactory;

        _logger =
            logger;
    }

    public async Task<AppObservationResponse> ReportAsync(
        Guid deviceUuid,
        string deviceSecret,
        AppObservationRequest request,
        CancellationToken cancellationToken)
    {
        if (deviceUuid == Guid.Empty)
        {
            throw new ArgumentException(
                "Device UUID cannot be empty.",
                nameof(deviceUuid));
        }

        if (string.IsNullOrWhiteSpace(
            deviceSecret))
        {
            throw new ArgumentException(
                "Device secret cannot be empty.",
                nameof(deviceSecret));
        }

        ArgumentNullException.ThrowIfNull(
            request);

        HttpClient client =
            _httpClientFactory.CreateClient(
                WorkforceApiClient.HttpClientName);

        using HttpRequestMessage message =
            new(
                HttpMethod.Post,
                ObservationPath);

        message.Headers.TryAddWithoutValidation(
            DeviceUuidHeader,
            deviceUuid.ToString());

        message.Headers.TryAddWithoutValidation(
            DeviceSecretHeader,
            deviceSecret);

        message.Content =
            JsonContent.Create(
                request);

        using HttpResponseMessage response =
            await client.SendAsync(
                message,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken);

        if (!response.IsSuccessStatusCode)
        {
            string body =
                await response.Content.ReadAsStringAsync(
                    cancellationToken);

            _logger.LogWarning(
                "WorkforceOS app observation API returned {StatusCode}. Body={Body}",
                (int)response.StatusCode,
                body);

            response.EnsureSuccessStatusCode();
        }

        AppObservationResponse? result =
            await response.Content
                .ReadFromJsonAsync<AppObservationResponse>(
                    cancellationToken:
                        cancellationToken);

        if (result is null)
        {
            throw new InvalidOperationException(
                "WorkforceOS app observation API returned an empty response.");
        }

        if (result.DeviceUuid != deviceUuid)
        {
            throw new InvalidOperationException(
                "WorkforceOS app observation API returned a mismatched device UUID.");
        }

        return result;
    }
}