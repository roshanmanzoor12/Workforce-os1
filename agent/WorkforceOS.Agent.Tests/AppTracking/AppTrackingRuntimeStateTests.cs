using WorkforceOS.Agent.AppTracking;

namespace WorkforceOS.Agent.Tests.AppTracking;

public sealed class AppTrackingRuntimeStateTests
{
    [Fact]
    public void RecordObservation_UpdatesLatestState()
    {
        AppTrackingRuntimeState state =
            new();

        AppTrackingSessionObservation observation =
            new()
            {
                SessionId = 1,

                UserSid =
                    "S-1-5-21-1000-1000-1000-1001",

                ProcessName =
                    "code.exe",

                ObservedAt =
                    DateTimeOffset.UtcNow,
            };

        state.RecordObservation(
            observation);

        AppTrackingRuntimeSnapshot snapshot =
            state.Snapshot();

        Assert.NotNull(
            snapshot.LatestObservation);

        Assert.Equal(
            "code.exe",
            snapshot
                .LatestObservation!
                .ProcessName);

        Assert.NotNull(
            snapshot.LastReceivedAt);

        Assert.Null(
            snapshot.LastError);
    }

    [Fact]
    public void RecordReported_UpdatesReportTimestamp()
    {
        AppTrackingRuntimeState state =
            new();

        DateTimeOffset timestamp =
            DateTimeOffset.UtcNow;

        state.RecordReported(
            timestamp);

        AppTrackingRuntimeSnapshot snapshot =
            state.Snapshot();

        Assert.Equal(
            timestamp,
            snapshot.LastReportedAt);
    }

    [Fact]
    public void RecordError_StoresError()
    {
        AppTrackingRuntimeState state =
            new();

        state.RecordError(
            new InvalidOperationException(
                "test-error"));

        AppTrackingRuntimeSnapshot snapshot =
            state.Snapshot();

        Assert.Equal(
            "test-error",
            snapshot.LastError);
    }
}