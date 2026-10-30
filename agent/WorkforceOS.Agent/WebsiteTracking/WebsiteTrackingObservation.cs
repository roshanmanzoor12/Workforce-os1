namespace WorkforceOS.Agent.WebsiteTracking;

public sealed record WebsiteTrackingObservation
{
    public required string BrowserName
    {
        get;
        init;
    }

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