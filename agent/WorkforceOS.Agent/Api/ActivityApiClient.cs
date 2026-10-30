using System.Net.Http.Json;
using System.Text.Json;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Api;

public sealed class ActivityApiClient
{
    private const string DeviceUuidHeaderName =
        "X-Device-UUID";

    private const string DeviceSecretHeaderName =
        "X-Device-Secret";

    private const string ActivityStatePath =
        "/api/v1/device-agent/activity-state";

    private const string ActivityStatusPath =
        "/api/v1/device-agent/activity-status";

    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web);

    private readonly IHttpClientFactory
        _httpClientFactory;

    public ActivityApiClient(
        IHttpClientFactory httpClientFactory
    )
    {
        _httpClientFactory =
            httpClientFactory;
    }

    public async Task<ActivityStateResponse>
        ReportStateAsync(
            DeviceCredentials credentials,
            ActivityStateRequest payload,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        ArgumentNullException.ThrowIfNull(
            payload
        );

        ValidateCredentials(
            credentials
        );

        using HttpClient client =
            _httpClientFactory.CreateClient(
                WorkforceApiClient.HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Post,
                ActivityStatePath
            );

        AddDeviceAuthenticationHeaders(
            request,
            credentials
        );

        request.Content =
            JsonContent.Create(
                payload,
                options: JsonOptions
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
                    "Activity state request failed " +
                    $"with HTTP status {(int)response.StatusCode}."
                ),
                response.StatusCode
            );
        }

        ActivityStateResponse? result =
            await response.Content
                .ReadFromJsonAsync<
                    ActivityStateResponse
                >(
                    JsonOptions,
                    cancellationToken
                );

        if (
            result is null
        )
        {
            throw new WorkforceApiException(
                "Activity state request returned an empty response.",
                response.StatusCode
            );
        }

        if (
            result.DeviceUuid
            != credentials.DeviceUuid
        )
        {
            throw new WorkforceApiException(
                "Activity response device identity does not match local credentials.",
                response.StatusCode
            );
        }

        return result;
    }

    public async Task<ActivityStatusResponse>
        GetStatusAsync(
            DeviceCredentials credentials,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        ValidateCredentials(
            credentials
        );

        using HttpClient client =
            _httpClientFactory.CreateClient(
                WorkforceApiClient.HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Get,
                ActivityStatusPath
            );

        AddDeviceAuthenticationHeaders(
            request,
            credentials
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
                    "Activity status request failed " +
                    $"with HTTP status {(int)response.StatusCode}."
                ),
                response.StatusCode
            );
        }

        ActivityStatusResponse? result =
            await response.Content
                .ReadFromJsonAsync<
                    ActivityStatusResponse
                >(
                    JsonOptions,
                    cancellationToken
                );

        if (
            result is null
        )
        {
            throw new WorkforceApiException(
                "Activity status request returned an empty response.",
                response.StatusCode
            );
        }

        if (
            result.DeviceUuid
            != credentials.DeviceUuid
        )
        {
            throw new WorkforceApiException(
                "Activity status identity does not match local credentials.",
                response.StatusCode
            );
        }

        return result;
    }

    private static void ValidateCredentials(
        DeviceCredentials credentials
    )
    {
        if (
            !credentials.IsValid()
        )
        {
            throw new ArgumentException(
                "Device credentials are invalid.",
                nameof(credentials)
            );
        }
    }

    private static void AddDeviceAuthenticationHeaders(
        HttpRequestMessage request,
        DeviceCredentials credentials
    )
    {
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
    }
}