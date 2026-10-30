using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Api;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingApiClient
{
    public const string ObservationPath =
        "/api/v1/device-agent/website-observation";

    private static readonly
        JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web)
            {
                PropertyNameCaseInsensitive =
                    true,
            };

    private readonly
        IHttpClientFactory
        _httpClientFactory;

    private readonly
        ILogger<
            WebsiteTrackingApiClient
        >
        _logger;

    public WebsiteTrackingApiClient(
        IHttpClientFactory httpClientFactory,
        ILogger<
            WebsiteTrackingApiClient
        > logger
    )
    {
        _httpClientFactory =
            httpClientFactory;

        _logger =
            logger;
    }

    public async Task<
        WebsiteTrackingApiObservationResponse?
    > ReportObservationAsync(
        WebsiteTrackingObservation observation,
        WebsiteTrackingDeviceCredentials credentials,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        ArgumentNullException.ThrowIfNull(
            credentials
        );

        if (
            !credentials.IsValid()
        )
        {
            throw new ArgumentException(
                "Website Tracking device credentials are invalid.",
                nameof(credentials)
            );
        }

        WebsiteTrackingApiObservationRequest payload =
            WebsiteTrackingApiObservationRequest
                .FromObservation(
                    observation
                );

        HttpClient client =
            _httpClientFactory.CreateClient(
                WorkforceApiClient
                    .HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Post,
                ObservationPath
            );

        request.Headers.Add(
            "X-Device-UUID",
            credentials.DeviceUuid
        );

        request.Headers.Add(
            "X-Device-Secret",
            credentials.DeviceSecret
        );

        request.Content =
            JsonContent.Create(
                payload,
                options:
                    JsonOptions
            );

        using HttpResponseMessage response =
            await client.SendAsync(
                request,
                HttpCompletionOption
                    .ResponseHeadersRead,
                cancellationToken
            );

        if (
            response.StatusCode
            == HttpStatusCode.Unauthorized
        )
        {
            _logger.LogWarning(
                "Website Tracking backend authentication failed."
            );

            return null;
        }

        if (
            !response.IsSuccessStatusCode
        )
        {
            _logger.LogWarning(
                "Website Tracking backend returned HTTP {StatusCode}.",
                (int)response.StatusCode
            );

            return null;
        }

        if (
            response.Content.Headers
                .ContentLength == 0
        )
        {
            return new WebsiteTrackingApiObservationResponse();
        }

        try
        {
            await using Stream stream =
                await response.Content
                    .ReadAsStreamAsync(
                        cancellationToken
                    );

            WebsiteTrackingApiObservationResponse?
                result =
                    await JsonSerializer
                        .DeserializeAsync<
                            WebsiteTrackingApiObservationResponse
                        >(
                            stream,
                            JsonOptions,
                            cancellationToken
                        );

            return (
                result
                ?? new WebsiteTrackingApiObservationResponse()
            );
        }
        catch (
            JsonException
        )
        {
            /*
             * HTTP success is authoritative here.
             * Response fields may evolve independently
             * from the Agent's reporting acknowledgement.
             */
            return new WebsiteTrackingApiObservationResponse();
        }
    }
}