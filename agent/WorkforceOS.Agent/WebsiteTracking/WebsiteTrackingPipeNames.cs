namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingPipeNames
{
    public const string ObservationPipe =
        "WorkforceOS.Agent.WebsiteTracking.v1";

    public const int MaximumMessageBytes =
        32 * 1024;

    public const int ProtocolVersion =
        1;
}