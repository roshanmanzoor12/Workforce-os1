using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class
    DeviceCredentialStoreWebsiteTrackingAdapter
    : IWebsiteTrackingCredentialProvider
{
    private readonly
        DeviceCredentialStore
        _credentialStore;

    private readonly
        ILogger<
            DeviceCredentialStoreWebsiteTrackingAdapter
        >
        _logger;

    public DeviceCredentialStoreWebsiteTrackingAdapter(
        DeviceCredentialStore credentialStore,
        ILogger<
            DeviceCredentialStoreWebsiteTrackingAdapter
        > logger
    )
    {
        _credentialStore =
            credentialStore;

        _logger =
            logger;
    }

    public async Task<
        WebsiteTrackingDeviceCredentials?
    > GetCredentialsAsync(
        CancellationToken cancellationToken
    )
    {
        DeviceCredentials? credentials =
            await _credentialStore.LoadAsync(
                cancellationToken
            );

        if (
            credentials is null
        )
        {
            _logger.LogDebug(
                "Website Tracking device credentials are not available."
            );

            return null;
        }

        if (
            !WebsiteTrackingCredentialProjection
                .TryProject(
                    credentials,
                    out WebsiteTrackingDeviceCredentials
                        projected
                )
        )
        {
            _logger.LogWarning(
                "Stored device credentials could not be projected for Website Tracking."
            );

            return null;
        }

        return projected;
    }
}