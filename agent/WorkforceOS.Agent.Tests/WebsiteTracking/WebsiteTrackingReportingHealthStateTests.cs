using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingReportingHealthStateTests
{
    [Fact]
    public void InitialStateIsEmpty()
    {
        WebsiteTrackingReportingHealthState state =
            new();

        WebsiteTrackingReportingHealthSnapshot snapshot =
            state.Snapshot();

        Assert.Equal(
            0,
            snapshot.SuccessCount
        );

        Assert.Equal(
            0,
            snapshot.FailureCount
        );

        Assert.Null(
            snapshot.LastSuccessAt
        );

        Assert.Null(
            snapshot.LastFailureAt
        );
    }

    [Fact]
    public void SuccessIsRecorded()
    {
        WebsiteTrackingReportingHealthState state =
            new();

        state.RecordSuccess();

        WebsiteTrackingReportingHealthSnapshot snapshot =
            state.Snapshot();

        Assert.Equal(
            1,
            snapshot.SuccessCount
        );

        Assert.NotNull(
            snapshot.LastSuccessAt
        );
    }

    [Fact]
    public void FailureIsRecorded()
    {
        WebsiteTrackingReportingHealthState state =
            new();

        state.RecordFailure(
            "test failure"
        );

        WebsiteTrackingReportingHealthSnapshot snapshot =
            state.Snapshot();

        Assert.Equal(
            1,
            snapshot.FailureCount
        );

        Assert.Equal(
            "test failure",
            snapshot.LastFailure
        );

        Assert.NotNull(
            snapshot.LastFailureAt
        );
    }
}