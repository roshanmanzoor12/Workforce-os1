namespace WorkforceOS.Agent.WebsiteTracking;

public sealed record WebsiteTrackingPipeAck
{
    public required bool Accepted
    {
        get;
        init;
    }

    public string? Error
    {
        get;
        init;
    }

    public static WebsiteTrackingPipeAck Success()
    {
        return new WebsiteTrackingPipeAck
        {
            Accepted =
                true,
        };
    }

    public static WebsiteTrackingPipeAck Reject(
        string error
    )
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(
            error
        );

        return new WebsiteTrackingPipeAck
        {
            Accepted =
                false,

            Error =
                error,
        };
    }
}