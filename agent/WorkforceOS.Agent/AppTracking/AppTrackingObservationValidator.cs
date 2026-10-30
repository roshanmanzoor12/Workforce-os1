using System.Security.Principal;

namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingObservationValidator
{
    private static readonly TimeSpan MaximumFutureSkew =
        TimeSpan.FromMinutes(
            2);

    private static readonly TimeSpan MaximumObservationAge =
        TimeSpan.FromMinutes(
            10);

    public void Validate(
        AppTrackingSessionObservation observation,
        string connectedUserSid)
    {
        ArgumentNullException.ThrowIfNull(
            observation);

        observation.Validate();

        if (string.IsNullOrWhiteSpace(
            connectedUserSid))
        {
            throw new UnauthorizedAccessException(
                "Unable to determine AppTracking client Windows SID.");
        }

        SecurityIdentifier actualSid =
            new(
                connectedUserSid);

        SecurityIdentifier declaredSid =
            new(
                observation.UserSid);

        if (!actualSid.Equals(
            declaredSid))
        {
            throw new UnauthorizedAccessException(
                "AppTracking client SID does not match observation UserSid.");
        }

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        if (
            observation.ObservedAt
            > now + MaximumFutureSkew)
        {
            throw new InvalidOperationException(
                "AppTracking observation timestamp is too far in the future.");
        }

        if (
            observation.ObservedAt
            < now - MaximumObservationAge)
        {
            throw new InvalidOperationException(
                "AppTracking observation is too old.");
        }

        if (observation.SessionId <= 0)
        {
            throw new UnauthorizedAccessException(
                "AppTracking observation did not originate from an interactive Windows session.");
        }
    }
}