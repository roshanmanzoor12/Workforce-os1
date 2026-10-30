namespace WorkforceOS.Agent.Activity;

public sealed class ActivityObservationValidator
{
    private static readonly TimeSpan
        MaximumFutureSkew =
            TimeSpan.FromMinutes(
                2
            );

    private static readonly TimeSpan
        MaximumObservationAge =
            TimeSpan.FromMinutes(
                10
            );

    public void Validate(
        ActivitySessionObservation observation,
        string connectedUserSid,
        DateTimeOffset? serverNow = null
    )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        if (
            string.IsNullOrWhiteSpace(
                connectedUserSid
            )
        )
        {
            throw new InvalidOperationException(
                "Connected pipe client SID is unavailable."
            );
        }

        observation.Validate();

        if (
            observation.SessionId
            <= 0
        )
        {
            throw new InvalidOperationException(
                "Activity observations must originate from an interactive Windows session."
            );
        }

        if (
            !string.Equals(
                observation.UserSid,
                connectedUserSid,
                StringComparison.OrdinalIgnoreCase
            )
        )
        {
            throw new UnauthorizedAccessException(
                "Activity observation user SID does not match the connected Windows identity."
            );
        }

        DateTimeOffset now =
            serverNow
            ?? DateTimeOffset.UtcNow;

        if (
            observation.ObservedAt
            > now + MaximumFutureSkew
        )
        {
            throw new InvalidOperationException(
                "Activity observation timestamp is too far in the future."
            );
        }

        if (
            observation.ObservedAt
            < now - MaximumObservationAge
        )
        {
            throw new InvalidOperationException(
                "Activity observation is too old."
            );
        }

        TimeSpan calculatedIdle =
            observation.ObservedAt
            - observation.LastInputAt;

        if (
            calculatedIdle
            < TimeSpan.Zero
        )
        {
            throw new InvalidOperationException(
                "Activity last-input timestamp is invalid."
            );
        }

        long calculatedIdleSeconds =
            (long)Math.Floor(
                calculatedIdle.TotalSeconds
            );

        long difference =
            Math.Abs(
                calculatedIdleSeconds
                - observation.IdleSeconds
            );

        if (
            difference
            > 5
        )
        {
            throw new InvalidOperationException(
                "Activity idle duration does not match the supplied timestamps."
            );
        }
    }
}