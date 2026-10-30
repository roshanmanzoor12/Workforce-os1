namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingPipeDiagnostics
{
    private long _acceptedConnections;
    private long _rejectedConnections;
    private long _acceptedObservations;
    private long _failedConnections;

    public void RecordConnectionAccepted()
    {
        Interlocked.Increment(
            ref _acceptedConnections
        );
    }

    public void RecordConnectionRejected()
    {
        Interlocked.Increment(
            ref _rejectedConnections
        );
    }

    public void RecordObservationAccepted()
    {
        Interlocked.Increment(
            ref _acceptedObservations
        );
    }

    public void RecordConnectionFailure()
    {
        Interlocked.Increment(
            ref _failedConnections
        );
    }

    public WebsiteTrackingPipeDiagnosticsSnapshot
        Snapshot()
    {
        return new WebsiteTrackingPipeDiagnosticsSnapshot(
            AcceptedConnections:
                Interlocked.Read(
                    ref _acceptedConnections
                ),

            RejectedConnections:
                Interlocked.Read(
                    ref _rejectedConnections
                ),

            AcceptedObservations:
                Interlocked.Read(
                    ref _acceptedObservations
                ),

            FailedConnections:
                Interlocked.Read(
                    ref _failedConnections
                )
        );
    }
}


public sealed record
    WebsiteTrackingPipeDiagnosticsSnapshot(
        long AcceptedConnections,
        long RejectedConnections,
        long AcceptedObservations,
        long FailedConnections
    );