namespace WorkforceOS.Agent.WebsiteTracking;

public interface IWebsiteTrackingCredentialProvider
{
    Task<WebsiteTrackingDeviceCredentials?>
        GetCredentialsAsync(
            CancellationToken cancellationToken
        );
}