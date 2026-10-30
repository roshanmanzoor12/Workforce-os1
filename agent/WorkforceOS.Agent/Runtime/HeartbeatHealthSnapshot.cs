namespace WorkforceOS.Agent.Runtime;

public sealed record HeartbeatHealthSnapshot
{
    public required Guid DeviceUuid
    {
        get;
        init;
    }

    public required bool HasSuccessfulHeartbeat
    {
        get;
        init;
    }

    public DateTimeOffset? LastSuccessfulHeartbeatAt
    {
        get;
        init;
    }

    public int ConsecutiveFailures
    {
        get;
        init;
    }

    public int CurrentHeartbeatIntervalSeconds
    {
        get;
        init;
    }

    public string? LastKnownDeviceStatus
    {
        get;
        init;
    }
}