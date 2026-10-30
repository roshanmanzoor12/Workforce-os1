using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingPipeDiagnosticsTests
{
    [Fact]
    public void InitialSnapshotIsZero()
    {
        WebsiteTrackingPipeDiagnostics diagnostics =
            new();

        WebsiteTrackingPipeDiagnosticsSnapshot snapshot =
            diagnostics.Snapshot();

        Assert.Equal(
            0,
            snapshot.AcceptedConnections
        );

        Assert.Equal(
            0,
            snapshot.RejectedConnections
        );

        Assert.Equal(
            0,
            snapshot.AcceptedObservations
        );

        Assert.Equal(
            0,
            snapshot.FailedConnections
        );
    }

    [Fact]
    public void CountersIncrement()
    {
        WebsiteTrackingPipeDiagnostics diagnostics =
            new();

        diagnostics.RecordConnectionAccepted();
        diagnostics.RecordConnectionAccepted();

        diagnostics.RecordConnectionRejected();

        diagnostics.RecordObservationAccepted();

        diagnostics.RecordConnectionFailure();

        WebsiteTrackingPipeDiagnosticsSnapshot snapshot =
            diagnostics.Snapshot();

        Assert.Equal(
            2,
            snapshot.AcceptedConnections
        );

        Assert.Equal(
            1,
            snapshot.RejectedConnections
        );

        Assert.Equal(
            1,
            snapshot.AcceptedObservations
        );

        Assert.Equal(
            1,
            snapshot.FailedConnections
        );
    }
}