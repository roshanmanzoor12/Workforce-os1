using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingRuntimeStateTests
{
    [Fact]
    public void InitialStateIsEmpty()
    {
        WebsiteTrackingRuntimeState
            state =
                new();

        WebsiteTrackingRuntimeSnapshot
            snapshot =
                state.Snapshot();

        Assert.Null(
            snapshot.LatestObservation
        );

        Assert.Null(
            snapshot.LatestReceivedAt
        );

        Assert.Equal(
            0,
            snapshot.AcceptedCount
        );

        Assert.Equal(
            0,
            snapshot.RejectedCount
        );
    }

    [Fact]
    public void AcceptUpdatesState()
    {
        WebsiteTrackingRuntimeState
            state =
                new();

        WebsiteTrackingObservation
            observation =
                new()
                {
                    BrowserName =
                        "Google Chrome",

                    BrowserProcessName =
                        "chrome.exe",

                    Domain =
                        "github.com",

                    ObservedAt =
                        DateTimeOffset.UtcNow,
                };

        state.Accept(
            observation
        );

        WebsiteTrackingRuntimeSnapshot
            snapshot =
                state.Snapshot();

        Assert.NotNull(
            snapshot.LatestObservation
        );

        Assert.Equal(
            "github.com",
            snapshot.LatestObservation!
                .Domain
        );

        Assert.Equal(
            1,
            snapshot.AcceptedCount
        );
    }

    [Fact]
    public void RejectIncrementsCount()
    {
        WebsiteTrackingRuntimeState
            state =
                new();

        state.Reject();
        state.Reject();

        Assert.Equal(
            2,
            state.Snapshot()
                .RejectedCount
        );
    }
}