using WorkforceOS.Agent.AppTracking;

namespace WorkforceOS.Agent.Tests.AppTracking;

public sealed class AppTrackingPipeProtocolTests
{
    [Fact]
    public async Task Protocol_RoundTripsObservation()
    {
        AppTrackingSessionObservation observation =
            new()
            {
                SessionId = 2,
                UserSid =
                    "S-1-5-21-1000-1000-1000-1001",
                ProcessName =
                    "code.exe",
                ExecutablePath =
                    @"C:\Code.exe",
                WindowTitle = null,
                ObservedAt =
                    DateTimeOffset.UtcNow,
            };

        await using MemoryStream stream =
            new();

        await AppTrackingPipeProtocol.WriteAsync(
            stream,
            observation,
            CancellationToken.None);

        stream.Position = 0;

        AppTrackingSessionObservation result =
            await AppTrackingPipeProtocol.ReadAsync(
                stream,
                CancellationToken.None);

        Assert.Equal(
            observation.SessionId,
            result.SessionId);

        Assert.Equal(
            observation.UserSid,
            result.UserSid);

        Assert.Equal(
            observation.ProcessName,
            result.ProcessName);
    }

    [Fact]
    public async Task Protocol_RejectsInvalidPayloadLength()
    {
        await using MemoryStream stream =
            new();

        byte[] invalidLength =
            BitConverter.GetBytes(
                AppTrackingPipeNames.MaximumMessageBytes
                + 1);

        await stream.WriteAsync(
            invalidLength);

        stream.Position = 0;

        await Assert.ThrowsAsync<InvalidDataException>(
            async () =>
                await AppTrackingPipeProtocol.ReadAsync(
                    stream,
                    CancellationToken.None));
    }
}