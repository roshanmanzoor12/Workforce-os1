using WorkforceOS.Agent.Activity;

namespace WorkforceOS.Agent.Tests.Activity;

public sealed class ActivityPipeProtocolTests
{
    [Fact]
    public void SerializeAndDeserialize_RoundTripsObservation()
    {
        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation input =
            new()
            {
                SessionId =
                    3,

                UserSid =
                    "S-1-5-21-1000-2000-3000-1001",

                State =
                    ActivityStateTracker.ActiveState,

                IdleSeconds =
                    25,

                LastInputAt =
                    now.AddSeconds(
                        -25
                    ),

                ObservedAt =
                    now
            };

        byte[] payload =
            ActivityPipeProtocol.Serialize(
                input
            );

        ActivitySessionObservation output =
            ActivityPipeProtocol.Deserialize(
                payload
            );

        Assert.Equal(
            input.ProtocolVersion,
            output.ProtocolVersion
        );

        Assert.Equal(
            input.SessionId,
            output.SessionId
        );

        Assert.Equal(
            input.UserSid,
            output.UserSid
        );

        Assert.Equal(
            input.State,
            output.State
        );

        Assert.Equal(
            input.IdleSeconds,
            output.IdleSeconds
        );

        Assert.Equal(
            input.LastInputAt,
            output.LastInputAt
        );

        Assert.Equal(
            input.ObservedAt,
            output.ObservedAt
        );
    }

    [Fact]
    public async Task WriteAndReadAsync_RoundTripsObservation()
    {
        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        ActivitySessionObservation input =
            new()
            {
                SessionId =
                    2,

                UserSid =
                    "S-1-5-21-10-20-30-1001",

                State =
                    ActivityStateTracker.IdleState,

                IdleSeconds =
                    600,

                LastInputAt =
                    now.AddSeconds(
                        -600
                    ),

                ObservedAt =
                    now
            };

        await using MemoryStream stream =
            new();

        await ActivityPipeProtocol.WriteAsync(
            stream,
            input
        );

        stream.Position =
            0;

        ActivitySessionObservation output =
            await ActivityPipeProtocol
                .ReadAsync(
                    stream
                );

        Assert.Equal(
            input.SessionId,
            output.SessionId
        );

        Assert.Equal(
            input.State,
            output.State
        );

        Assert.Equal(
            input.IdleSeconds,
            output.IdleSeconds
        );
    }

    [Fact]
    public void Deserialize_RejectsEmptyPayload()
    {
        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                ActivityPipeProtocol.Deserialize(
                    Array.Empty<byte>()
                );
            }
        );
    }

    [Fact]
    public void Deserialize_RejectsOversizedPayload()
    {
        byte[] payload =
            new byte[
                ActivityPipeProtocol
                    .MaximumPayloadBytes
                + 1
            ];

        Assert.Throws<
            InvalidOperationException
        >(
            () =>
            {
                ActivityPipeProtocol.Deserialize(
                    payload
                );
            }
        );
    }

    [Fact]
    public async Task ReadAsync_RejectsOversizedLengthPrefix()
    {
        await using MemoryStream stream =
            new();

        byte[] prefix =
            BitConverter.GetBytes(
                ActivityPipeProtocol
                    .MaximumPayloadBytes
                + 1
            );

        await stream.WriteAsync(
            prefix
        );

        stream.Position =
            0;

        await Assert.ThrowsAsync<
            InvalidOperationException
        >(
            async () =>
            {
                await ActivityPipeProtocol
                    .ReadAsync(
                        stream
                    );
            }
        );
    }
}