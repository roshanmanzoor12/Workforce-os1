namespace WorkforceOS.Agent.WebsiteTracking;

public sealed record BrowserBridgeMessage
{
    public int ProtocolVersion
    {
        get;
        init;
    } =
        WebsiteTrackingPipeNames
            .ProtocolVersion;

    public required string BrowserProcessName
    {
        get;
        init;
    }

    public required string Domain
    {
        get;
        init;
    }

    public string? PageUrl
    {
        get;
        init;
    }

    public string? PageTitle
    {
        get;
        init;
    }

    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }
}