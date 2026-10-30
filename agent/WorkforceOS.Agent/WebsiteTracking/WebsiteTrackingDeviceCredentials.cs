namespace WorkforceOS.Agent.WebsiteTracking;

public sealed record WebsiteTrackingDeviceCredentials
{
    public required string DeviceUuid
    {
        get;
        init;
    }

    public required string DeviceSecret
    {
        get;
        init;
    }

    public bool IsValid()
    {
        return (
            Guid.TryParse(
                DeviceUuid,
                out _
            )
            &&
            !string.IsNullOrWhiteSpace(
                DeviceSecret
            )
        );
    }
}