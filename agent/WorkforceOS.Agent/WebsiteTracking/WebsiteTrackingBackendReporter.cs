using Microsoft.Extensions.Logging;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingBackendReporter
{
    private readonly
        IWebsiteTrackingCredentialProvider
        _credentialProvider;

    private readonly
        WebsiteTrackingApiClient
        _apiClient;

    private readonly
        WebsiteTrackingReportingHealthState
        _healthState;

    private readonly
        ILogger<
            WebsiteTrackingBackendReporter
        >
        _logger;

    public WebsiteTrackingBackendReporter(
        IWebsiteTrackingCredentialProvider credentialProvider,
        WebsiteTrackingApiClient apiClient,
        WebsiteTrackingReportingHealthState healthState,
        ILogger<
            WebsiteTrackingBackendReporter
        > logger
    )
    {
        _credentialProvider =
            credentialProvider;

        _apiClient =
            apiClient;

        _healthState =
            healthState;

        _logger =
            logger;
    }

    public async Task<
        WebsiteTrackingReportResult
    > ReportAsync(
        WebsiteTrackingObservation observation,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        WebsiteTrackingDeviceCredentials?
            credentials =
                await _credentialProvider
                    .GetCredentialsAsync(
                        cancellationToken
                    );

        if (
            credentials is null
            || !credentials.IsValid()
        )
        {
            const string error =
                "Device credentials unavailable.";

            _healthState.RecordFailure(
                error
            );

            return new WebsiteTrackingReportResult
            {
                Status =
                    WebsiteTrackingReportStatus
                        .CredentialsUnavailable,

                Error =
                    error,
            };
        }

        try
        {
            WebsiteTrackingApiObservationResponse?
                response =
                    await _apiClient
                        .ReportObservationAsync(
                            observation,
                            credentials,
                            cancellationToken
                        );

            if (
                response is null
            )
            {
                const string error =
                    "Backend rejected Website Tracking observation.";

                _healthState.RecordFailure(
                    error
                );

                return new WebsiteTrackingReportResult
                {
                    Status =
                        WebsiteTrackingReportStatus
                            .BackendRejected,

                    Error =
                        error,
                };
            }

            _healthState.RecordSuccess();

            _logger.LogDebug(
                "Website Tracking observation reported. Browser={Browser}; Domain={Domain}.",
                observation.BrowserProcessName,
                observation.Domain
            );

            return new WebsiteTrackingReportResult
            {
                Status =
                    WebsiteTrackingReportStatus
                        .Success,
            };
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            throw;
        }
        catch (
            Exception exception
        )
        {
            _healthState.RecordFailure(
                exception.GetType().Name
            );

            _logger.LogWarning(
                exception,
                "Website Tracking reporting failed."
            );

            return new WebsiteTrackingReportResult
            {
                Status =
                    WebsiteTrackingReportStatus
                        .Failed,

                Error =
                    exception.GetType().Name,
            };
        }
    }
}