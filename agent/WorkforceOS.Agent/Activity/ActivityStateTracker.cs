namespace WorkforceOS.Agent.Activity;

public sealed class ActivityStateTracker
{
    public const string ActiveState =
        "active";

    public const string IdleState =
        "idle";

    private readonly int
        _idleThresholdSeconds;

    public ActivityStateTracker(
        int idleThresholdSeconds
    )
    {
        if (
            idleThresholdSeconds
            < 5
        )
        {
            throw new ArgumentOutOfRangeException(
                nameof(idleThresholdSeconds),
                "Idle threshold must be at least 5 seconds."
            );
        }

        _idleThresholdSeconds =
            idleThresholdSeconds;
    }

    public ActivityStateSnapshot Evaluate(
        LastInputSnapshot snapshot
    )
    {
        ArgumentNullException.ThrowIfNull(
            snapshot
        );

        long idleSeconds =
            Math.Max(
                0,
                snapshot.IdleSeconds
            );

        string state =
            idleSeconds
            >= _idleThresholdSeconds
                ? IdleState
                : ActiveState;

        return new ActivityStateSnapshot
        {
            State =
                state,

            IdleSeconds =
                idleSeconds,

            LastInputAt =
                snapshot.LastInputAt,

            ObservedAt =
                snapshot.ObservedAt
        };
    }
}


public sealed record ActivityStateSnapshot
{
    public required string State
    {
        get;
        init;
    }

    public required long IdleSeconds
    {
        get;
        init;
    }

    public required DateTimeOffset LastInputAt
    {
        get;
        init;
    }

    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }

    public bool IsIdle =>
        string.Equals(
            State,
            ActivityStateTracker.IdleState,
            StringComparison.Ordinal
        );

    public bool IsActive =>
        string.Equals(
            State,
            ActivityStateTracker.ActiveState,
            StringComparison.Ordinal
        );
}
