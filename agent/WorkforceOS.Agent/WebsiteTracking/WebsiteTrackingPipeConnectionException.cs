namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingPipeConnectionException
    : IOException
{
    public WebsiteTrackingPipeConnectionException(
        string message,
        Exception? innerException,
        int attempts
    )
        : base(
            message,
            innerException
        )
    {
        Attempts =
            attempts;

        LastExceptionType =
            innerException?
                .GetType()
                .Name;

        LastHResult =
            innerException?
                .HResult;
    }

    public int Attempts
    {
        get;
    }

    public string? LastExceptionType
    {
        get;
    }

    public int? LastHResult
    {
        get;
    }
}