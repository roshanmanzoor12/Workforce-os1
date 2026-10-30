namespace WorkforceOS.Agent.Api;

public sealed record DeviceAgentAuthenticationResult
{
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    public string? Status
    {
        get;
        init;
    }

    public DateTimeOffset AuthenticatedAt
    {
        get;
        init;
    } =
        DateTimeOffset.UtcNow;
}