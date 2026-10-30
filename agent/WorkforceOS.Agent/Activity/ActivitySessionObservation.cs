using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.Activity;

public sealed record ActivitySessionObservation
{
    public const int CurrentProtocolVersion =
        1;

    [JsonPropertyName("protocol_version")]
    public int ProtocolVersion
    {
        get;
        init;
    } = CurrentProtocolVersion;

    [JsonPropertyName("session_id")]
    public required int SessionId
    {
        get;
        init;
    }

    [JsonPropertyName("user_sid")]
    public required string UserSid
    {
        get;
        init;
    }

    [JsonPropertyName("state")]
    public required string State
    {
        get;
        init;
    }

    [JsonPropertyName("idle_seconds")]
    public required long IdleSeconds
    {
        get;
        init;
    }

    [JsonPropertyName("last_input_at")]
    public required DateTimeOffset LastInputAt
    {
        get;
        init;
    }

    [JsonPropertyName("observed_at")]
    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }

    public void Validate()
    {
        if (
            ProtocolVersion
            != CurrentProtocolVersion
        )
        {
            throw new InvalidOperationException(
                "Unsupported activity session protocol version."
            );
        }

        if (
            SessionId
            < 0
        )
        {
            throw new InvalidOperationException(
                "Windows session ID cannot be negative."
            );
        }

        if (
            string.IsNullOrWhiteSpace(
                UserSid
            )
        )
        {
            throw new InvalidOperationException(
                "Windows user SID is required."
            );
        }

        if (
            !string.Equals(
                State,
                ActivityStateTracker.ActiveState,
                StringComparison.Ordinal
            )
            &&
            !string.Equals(
                State,
                ActivityStateTracker.IdleState,
                StringComparison.Ordinal
            )
        )
        {
            throw new InvalidOperationException(
                "Activity state must be active or idle."
            );
        }

        if (
            IdleSeconds
            < 0
        )
        {
            throw new InvalidOperationException(
                "Idle seconds cannot be negative."
            );
        }

        if (
            LastInputAt
            > ObservedAt
        )
        {
            throw new InvalidOperationException(
                "Last input time cannot be later than observation time."
            );
        }
    }

    public ActivityStateSnapshot ToActivityStateSnapshot()
    {
        Validate();

        return new ActivityStateSnapshot
        {
            State =
                State,

            IdleSeconds =
                IdleSeconds,

            LastInputAt =
                LastInputAt,

            ObservedAt =
                ObservedAt
        };
    }
}