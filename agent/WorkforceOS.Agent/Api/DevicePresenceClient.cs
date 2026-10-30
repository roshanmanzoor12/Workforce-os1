using System.Net.Http.Json;
using System.Text.Json;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Api;

public sealed class DevicePresenceClient
{
    private const string DeviceUuidHeaderName =
        "X-Device-UUID";

    private const string DeviceSecretHeaderName =
        "X-Device-Secret";

    private const string PresencePath =
        "/api/v1/device-agent/presence";

    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web);

    private readonly IHttpClientFactory
        _httpClientFactory;

    public DevicePresenceClient(
        IHttpClientFactory httpClientFactory
    )
    {
        _httpClientFactory =
            httpClientFactory;
    }

    public async Task<DevicePresenceResponse>
        GetPresenceAsync(
            DeviceCredentials credentials,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        if (
            !credentials.IsValid()
        )
        {
            throw new ArgumentException(
                "Device credentials are invalid.",
                nameof(credentials)
            );
        }

        using HttpClient client =
            _httpClientFactory.CreateClient(
                WorkforceApiClient.HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Get,
                PresencePath
            );

        request.Headers.TryAddWithoutValidation(
            DeviceUuidHeaderName,
            credentials.DeviceUuid.ToString(
                "D"
            )
        );

        request.Headers.TryAddWithoutValidation(
            DeviceSecretHeaderName,
            credentials.DeviceSecret
        );

        using HttpResponseMessage response =
            await client.SendAsync(
                request,
                HttpCompletionOption.ResponseHeadersRead,
                cancellationToken
            );

        if (
            !response.IsSuccessStatusCode
        )
        {
            throw new WorkforceApiException(
                (
                    "Device presence request failed " +
                    $"with HTTP status " +
                    $"{(int)response.StatusCode}."
                ),
                response.StatusCode
            );
        }

        DevicePresenceResponse? result =
            await response.Content
                .ReadFromJsonAsync<
                    DevicePresenceResponse
                >(
                    JsonOptions,
                    cancellationToken
                );

        if (
            result is null
        )
        {
            throw new WorkforceApiException(
                "Device presence returned an empty response.",
                response.StatusCode
            );
        }

        if (
            result.DeviceUuid
            != credentials.DeviceUuid
        )
        {
            throw new WorkforceApiException(
                "Device presence identity does not match local enrollment.",
                response.StatusCode
            );
        }

        if (
            result.OnlineTimeoutSeconds
            is < 5 or > 3600
        )
        {
            throw new WorkforceApiException(
                "Device presence returned an invalid timeout.",
                response.StatusCode
            );
        }

        return result;
    }
}