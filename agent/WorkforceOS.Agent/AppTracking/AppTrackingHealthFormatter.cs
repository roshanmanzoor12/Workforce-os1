namespace WorkforceOS.Agent.AppTracking;

public static class AppTrackingHealthFormatter
{
    public static string Format(
        AppTrackingHealthSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(
            snapshot);

        string process =
            snapshot.CurrentProcessName
            ?? "(none)";

        string lastReceived =
            snapshot.LastReceivedAt?
                .ToString("O")
            ?? "(never)";

        string lastReported =
            snapshot.LastReportedAt?
                .ToString("O")
            ?? "(never)";

        string error =
            snapshot.LastError
            ?? "(none)";

        return string.Join(
            Environment.NewLine,
            new[]
            {
                $"Enabled: {snapshot.Enabled}",
                $"Healthy: {snapshot.IsHealthy}",
                $"Has interactive observation: {snapshot.HasInteractiveObservation}",
                $"Has backend report: {snapshot.HasBackendReport}",
                $"Current process: {process}",
                $"Last received: {lastReceived}",
                $"Last reported: {lastReported}",
                $"Last error: {error}",
            });
    }
}