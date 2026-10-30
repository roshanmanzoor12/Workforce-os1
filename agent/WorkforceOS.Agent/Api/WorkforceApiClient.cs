using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Configuration;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Api;

public sealed class WorkforceApiClient
{
    public const string HttpClientName =
        "WorkforceOSApi";

    private const string DeviceUuidHeaderName =
        "X-Device-UUID";

    private const string DeviceSecretHeaderName =
        "X-Device-Secret";

    private const string HeartbeatPath =
        "/api/v1/device-agent/heartbeat";

    private static readonly JsonSerializerOptions
        JsonOptions =
            new(JsonSerializerDefaults.Web);

    private readonly IHttpClientFactory
        _httpClientFactory;

    private readonly AgentOptions
        _options;

    public WorkforceApiClient(
        IHttpClientFactory httpClientFactory,
        IOptions<AgentOptions> options
    )
    {
        _httpClientFactory =
            httpClientFactory;

        _options =
            options.Value;
    }

    // =====================================================
    // DEVICE REGISTRATION
    // =====================================================

    public async Task<DeviceRegistrationResponse>
        RegisterDeviceAsync(
            DeviceRegistrationRequest request,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            request
        );

        using HttpClient client =
            _httpClientFactory.CreateClient(
                HttpClientName
            );

        using HttpResponseMessage response =
            await client.PostAsJsonAsync(
                _options.RegistrationPath,
                request,
                JsonOptions,
                cancellationToken
            );

        if (
            response.IsSuccessStatusCode
        )
        {
            DeviceRegistrationResponse? result =
                await response.Content
                    .ReadFromJsonAsync<
                        DeviceRegistrationResponse
                    >(
                        JsonOptions,
                        cancellationToken
                    );

            if (
                result is null
            )
            {
                throw new WorkforceApiException(
                    "Device registration returned an empty response.",
                    response.StatusCode
                );
            }

            ValidateRegistrationResponse(
                result
            );

            return result;
        }

        string responseBody =
            await ReadSafeResponseBodyAsync(
                response,
                cancellationToken
            );

        throw new WorkforceApiException(
            BuildApiErrorMessage(
                "Device registration",
                response.StatusCode,
                responseBody
            ),
            response.StatusCode
        );
    }

    // =====================================================
    // AUTHENTICATED DEVICE IDENTITY
    // =====================================================

    public async Task<DeviceAgentAuthenticationResult>
        AuthenticateDeviceAsync(
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
                HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Get,
                _options.DeviceIdentityPath
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
            string responseBody =
                await ReadSafeResponseBodyAsync(
                    response,
                    cancellationToken
                );

            throw new WorkforceApiException(
                BuildApiErrorMessage(
                    "Device authentication",
                    response.StatusCode,
                    responseBody
                ),
                response.StatusCode
            );
        }

        string body =
            await response.Content.ReadAsStringAsync(
                cancellationToken
            );

        if (
            string.IsNullOrWhiteSpace(
                body
            )
        )
        {
            throw new WorkforceApiException(
                "Device authentication returned an empty response.",
                response.StatusCode
            );
        }

        return ParseAuthenticationResponse(
            body,
            credentials.DeviceUuid,
            response.StatusCode
        );
    }

    // =====================================================
    // HEARTBEAT
    // =====================================================

    public async Task<DeviceHeartbeatResponse>
        SendHeartbeatAsync(
            DeviceCredentials credentials,
            DeviceHeartbeatRequest heartbeat,
            CancellationToken cancellationToken = default
        )
    {
        ArgumentNullException.ThrowIfNull(
            credentials
        );

        ArgumentNullException.ThrowIfNull(
            heartbeat
        );

        ValidateCredentials(
            credentials
        );

        using HttpClient client =
            _httpClientFactory.CreateClient(
                HttpClientName
            );

        using HttpRequestMessage request =
            new(
                HttpMethod.Post,
                HeartbeatPath
            );

        AddDeviceAuthenticationHeaders(
            request,
            credentials
        );

        request.Content =
            JsonContent.Create(
                heartbeat,
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
            string responseBody =
                await ReadSafeResponseBodyAsync(
                    response,
                    cancellationToken
                );

            throw new WorkforceApiException(
                BuildApiErrorMessage(
                    "Device heartbeat",
                    response.StatusCode,
                    responseBody
                ),
                response.StatusCode
            );
        }

        DeviceHeartbeatResponse? result =
            await response.Content
                .ReadFromJsonAsync<
                    DeviceHeartbeatResponse
                >(
                    JsonOptions,
                    cancellationToken
                );

        if (
            result is null
        )
        {
            throw new WorkforceApiException(
                "Device heartbeat returned an empty response.",
                response.StatusCode
            );
        }

        ValidateHeartbeatResponse(
            result,
            credentials.DeviceUuid,
            response.StatusCode
        );

        return result;
    }

    // =====================================================
    // DEVICE AUTH HEADERS
    // =====================================================

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

    // =====================================================
    // REGISTRATION RESPONSE
    // =====================================================

    private static void ValidateRegistrationResponse(
        DeviceRegistrationResponse response
    )
    {
        ArgumentNullException.ThrowIfNull(
            response
        );

        if (
            response.Device.Id
            == Guid.Empty
        )
        {
            throw new WorkforceApiException(
                "Registration response contains an invalid device ID."
            );
        }

        if (
            response.Device.DeviceUuid
            == Guid.Empty
        )
        {
            throw new WorkforceApiException(
                "Registration response contains an invalid device UUID."
            );
        }

        if (
            response.Credential.DeviceUuid
            == Guid.Empty
        )
        {
            throw new WorkforceApiException(
                "Registration response contains an invalid credential device UUID."
            );
        }

        if (
            response.Device.DeviceUuid
            != response.Credential.DeviceUuid
        )
        {
            throw new WorkforceApiException(
                "Registration response device identity does not match its credential."
            );
        }

        if (
            string.IsNullOrWhiteSpace(
                response.Credential.DeviceSecret
            )
        )
        {
            throw new WorkforceApiException(
                "Registration response did not contain a device credential."
            );
        }

        if (
            response.Credential.DeviceSecret.Length
            < 20
        )
        {
            throw new WorkforceApiException(
                "Registration response contained an invalid device credential."
            );
        }
    }

    // =====================================================
    // HEARTBEAT RESPONSE
    // =====================================================

    private static void ValidateHeartbeatResponse(
        DeviceHeartbeatResponse response,
        Guid expectedDeviceUuid,
        HttpStatusCode statusCode
    )
    {
        if (
            response.DeviceUuid
            == Guid.Empty
        )
        {
            throw new WorkforceApiException(
                "Heartbeat response contains an invalid device UUID.",
                statusCode
            );
        }

        if (
            response.DeviceUuid
            != expectedDeviceUuid
        )
        {
            throw new WorkforceApiException(
                "Heartbeat response device UUID does not match local credentials.",
                statusCode
            );
        }

        if (
            string.IsNullOrWhiteSpace(
                response.Status
            )
        )
        {
            throw new WorkforceApiException(
                "Heartbeat response contains an invalid device status.",
                statusCode
            );
        }

        if (
            response.NextHeartbeatSeconds
            is < 5 or > 300
        )
        {
            throw new WorkforceApiException(
                "Heartbeat response contains an invalid heartbeat interval.",
                statusCode
            );
        }
    }

    // =====================================================
    // AUTH RESPONSE PARSING
    // =====================================================

    private static DeviceAgentAuthenticationResult
        ParseAuthenticationResponse(
            string body,
            Guid expectedDeviceUuid,
            HttpStatusCode statusCode
        )
    {
        try
        {
            using JsonDocument document =
                JsonDocument.Parse(
                    body
                );

            if (
                !TryFindGuidProperty(
                    document.RootElement,
                    "device_uuid",
                    out Guid deviceUuid
                )
            )
            {
                throw new WorkforceApiException(
                    "Device authentication response did not contain a device UUID.",
                    statusCode
                );
            }

            if (
                deviceUuid
                != expectedDeviceUuid
            )
            {
                throw new WorkforceApiException(
                    "Authenticated device identity does not match local credentials.",
                    statusCode
                );
            }

            string? deviceStatus =
                TryFindStringProperty(
                    document.RootElement,
                    "status"
                );

            return new DeviceAgentAuthenticationResult
            {
                DeviceUuid =
                    deviceUuid,

                Status =
                    deviceStatus,

                AuthenticatedAt =
                    DateTimeOffset.UtcNow
            };
        }
        catch (
            JsonException exception
        )
        {
            throw new WorkforceApiException(
                "Device authentication returned invalid JSON.",
                statusCode,
                exception
            );
        }
    }

    private static bool TryFindGuidProperty(
        JsonElement element,
        string propertyName,
        out Guid value
    )
    {
        value =
            Guid.Empty;

        if (
            element.ValueKind
            == JsonValueKind.Object
        )
        {
            foreach (
                JsonProperty property
                in element.EnumerateObject()
            )
            {
                if (
                    string.Equals(
                        property.Name,
                        propertyName,
                        StringComparison.OrdinalIgnoreCase
                    )
                    && property.Value.ValueKind
                    == JsonValueKind.String
                    && Guid.TryParse(
                        property.Value.GetString(),
                        out value
                    )
                )
                {
                    return true;
                }

                if (
                    TryFindGuidProperty(
                        property.Value,
                        propertyName,
                        out value
                    )
                )
                {
                    return true;
                }
            }
        }
        else if (
            element.ValueKind
            == JsonValueKind.Array
        )
        {
            foreach (
                JsonElement child
                in element.EnumerateArray()
            )
            {
                if (
                    TryFindGuidProperty(
                        child,
                        propertyName,
                        out value
                    )
                )
                {
                    return true;
                }
            }
        }

        return false;
    }

    private static string? TryFindStringProperty(
        JsonElement element,
        string propertyName
    )
    {
        if (
            element.ValueKind
            == JsonValueKind.Object
        )
        {
            foreach (
                JsonProperty property
                in element.EnumerateObject()
            )
            {
                if (
                    string.Equals(
                        property.Name,
                        propertyName,
                        StringComparison.OrdinalIgnoreCase
                    )
                    && property.Value.ValueKind
                    == JsonValueKind.String
                )
                {
                    return property.Value.GetString();
                }

                string? nestedValue =
                    TryFindStringProperty(
                        property.Value,
                        propertyName
                    );

                if (
                    nestedValue is not null
                )
                {
                    return nestedValue;
                }
            }
        }
        else if (
            element.ValueKind
            == JsonValueKind.Array
        )
        {
            foreach (
                JsonElement child
                in element.EnumerateArray()
            )
            {
                string? nestedValue =
                    TryFindStringProperty(
                        child,
                        propertyName
                    );

                if (
                    nestedValue is not null
                )
                {
                    return nestedValue;
                }
            }
        }

        return null;
    }

    // =====================================================
    // SAFE ERROR HANDLING
    // =====================================================

    private static string BuildApiErrorMessage(
        string operationName,
        HttpStatusCode statusCode,
        string responseBody
    )
    {
        string? serverMessage =
            TryExtractSafeErrorMessage(
                responseBody
            );

        if (
            !string.IsNullOrWhiteSpace(
                serverMessage
            )
        )
        {
            return
                $"{operationName} failed " +
                $"({(int)statusCode}): " +
                serverMessage;
        }

        return
            $"{operationName} failed " +
            $"with HTTP status {(int)statusCode}.";
    }

    private static string? TryExtractSafeErrorMessage(
        string responseBody
    )
    {
        if (
            string.IsNullOrWhiteSpace(
                responseBody
            )
        )
        {
            return null;
        }

        try
        {
            using JsonDocument document =
                JsonDocument.Parse(
                    responseBody
                );

            JsonElement root =
                document.RootElement;

            if (
                root.TryGetProperty(
                    "error",
                    out JsonElement errorElement
                )
                && errorElement.ValueKind
                == JsonValueKind.Object
                && errorElement.TryGetProperty(
                    "message",
                    out JsonElement messageElement
                )
                && messageElement.ValueKind
                == JsonValueKind.String
            )
            {
                return NormalizeSafeMessage(
                    messageElement.GetString()
                );
            }

            if (
                root.TryGetProperty(
                    "detail",
                    out JsonElement detailElement
                )
                && detailElement.ValueKind
                == JsonValueKind.String
            )
            {
                return NormalizeSafeMessage(
                    detailElement.GetString()
                );
            }
        }
        catch (
            JsonException
        )
        {
            // Never expose arbitrary raw backend response bodies.
        }

        return null;
    }

    private static string? NormalizeSafeMessage(
        string? value
    )
    {
        if (
            string.IsNullOrWhiteSpace(
                value
            )
        )
        {
            return null;
        }

        string normalized =
            value.Trim();

        const int maximumLength =
            300;

        if (
            normalized.Length
            > maximumLength
        )
        {
            normalized =
                normalized[
                    ..maximumLength
                ];
        }

        return normalized;
    }

    private static async Task<string>
        ReadSafeResponseBodyAsync(
            HttpResponseMessage response,
            CancellationToken cancellationToken
        )
    {
        string body =
            await response.Content.ReadAsStringAsync(
                cancellationToken
            );

        const int maximumLength =
            4096;

        if (
            body.Length
            > maximumLength
        )
        {
            return body[
                ..maximumLength
            ];
        }

        return body;
    }
}


// =========================================================
// API EXCEPTION
// =========================================================

public sealed class WorkforceApiException
    : Exception
{
    public HttpStatusCode? StatusCode
    {
        get;
    }

    public WorkforceApiException(
        string message
    )
        : base(
            message
        )
    {
    }

    public WorkforceApiException(
        string message,
        HttpStatusCode statusCode
    )
        : base(
            message
        )
    {
        StatusCode =
            statusCode;
    }

    public WorkforceApiException(
        string message,
        HttpStatusCode statusCode,
        Exception innerException
    )
        : base(
            message,
            innerException
        )
    {
        StatusCode =
            statusCode;
    }
}