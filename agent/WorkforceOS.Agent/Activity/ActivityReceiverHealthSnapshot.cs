namespace WorkforceOS.Agent.Activity;

public sealed record ActivityReceiverHealthSnapshot
{
    public required bool HasObservation
    {
        get;
        init;
    }

    public int? SessionId
    {
        get;
        init;
    }

    public string? UserSid
    {
        get;
        init;
    }

    public string? State
    {
        get;
        init;
    }

    public long? IdleSeconds
    {
        get;
        init;
    }

    public DateTimeOffset? ObservedAt
    {
        get;
        init;
    }

    public DateTimeOffset? LastReceivedAt
    {
        get;
        init;
    }

    public DateTimeOffset? LastReportAt
    {
        get;
        init;
    }

    public string? LastError
    {
        get;
        init;
    }

    public bool IsHealthy(
        TimeSpan maximumObservationAge
    )
    {
        if (
            !HasObservation
            ||
            LastReceivedAt is null
        )
        {
            return false;
        }

        return (
            DateTimeOffset.UtcNow
            - LastReceivedAt.Value
        ) <= maximumObservationAge;
    }
}