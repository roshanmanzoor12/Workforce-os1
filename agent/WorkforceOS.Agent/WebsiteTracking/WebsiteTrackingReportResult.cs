namespace WorkforceOS.Agent.WebsiteTracking;

public enum WebsiteTrackingReportStatus
{
    Success = 0,
    CredentialsUnavailable = 1,
    BackendRejected = 2,
    Failed = 3,
}


public sealed record WebsiteTrackingReportResult
{
    public required WebsiteTrackingReportStatus
        Status
    {
        get;
        init;
    }

    public string? Error
    {
        get;
        init;
    }

    public bool IsSuccess =>
        Status
        == WebsiteTrackingReportStatus
            .Success;
}