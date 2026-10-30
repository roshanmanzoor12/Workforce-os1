using WorkforceOS.Agent.Activity;

namespace WorkforceOS.Agent.Tests.Activity;

public sealed class ActivityObservationValidatorTests
{
    private const string UserSid =
        "S-1-5-21-100-200-300-1001";

    [Fact]
    public void Validate_AcceptsValidObservation()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    2,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    30,

                LastInputAt =
                    now.AddSeconds(
                        -30
                    ),

                ObservedAt =
                    now
            };

        validator.Validate(
            observation,
            UserSid,
            now
        );
    }

    [Fact]
    public void Validate_RejectsDifferentConnectedUserSid()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    2,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    10,

                LastInputAt =
                    now.AddSeconds(
                        -10
                    ),

                ObservedAt =
                    now
            };

        Assert.Throws<
            UnauthorizedAccessException
        >(
            () =>
            {
                validator.Validate(
                    observation,
                    "S-1-5-21-999-999-999-1002",
                    now
                );
            }
        );
    }

    [Fact]
    public void Validate_RejectsSessionZero()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    0,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    0,

                LastInputAt =
                    now,

                ObservedAt =
                    now
            };

        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                validator.Validate(
                    observation,
                    UserSid,
                    now
                );
            }
        );
    }

    [Fact]
    public void Validate_RejectsOldObservation()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        DateTimeOffset observedAt =
            now.AddMinutes(
                -20
            );

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    3,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.IdleState,

                IdleSeconds =
                    60,

                LastInputAt =
                    observedAt.AddSeconds(
                        -60
                    ),

                ObservedAt =
                    observedAt
            };

        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                validator.Validate(
                    observation,
                    UserSid,
                    now
                );
            }
        );
    }

    [Fact]
    public void Validate_RejectsObservationTooFarInFuture()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        DateTimeOffset observedAt =
            now.AddMinutes(
                5
            );

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    3,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    5,

                LastInputAt =
                    observedAt.AddSeconds(
                        -5
                    ),

                ObservedAt =
                    observedAt
            };

        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                validator.Validate(
                    observation,
                    UserSid,
                    now
                );
            }
        );
    }

    [Fact]
    public void Validate_RejectsIdleDurationMismatch()
    {
        ActivityObservationValidator validator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation observation =
            new()
            {
                SessionId =
                    2,

                UserSid =
                    UserSid,

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    5,

                LastInputAt =
                    now.AddSeconds(
                        -100
                    ),

                ObservedAt =
                    now
            };

        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                validator.Validate(
                    observation,
                    UserSid,
                    now
                );
            }
        );
    }
}