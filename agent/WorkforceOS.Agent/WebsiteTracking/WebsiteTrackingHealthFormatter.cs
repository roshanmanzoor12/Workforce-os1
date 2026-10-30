namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingHealthFormatter
{
    public static string Format(
        WebsiteTrackingHealthSnapshot
            snapshot
    )
    {
        ArgumentNullException.ThrowIfNull(
            snapshot
        );

        if (
            !snapshot.HasObservation
        )
        {
            return (
                "Website Tracking: "
                + "no observation received"
            );
        }

        string browser =
            snapshot.BrowserProcessName
            ?? "unknown";

        string domain =
            snapshot.Domain
            ?? "unknown";

        string observedAt =
            snapshot.LastObservedAt?
                .ToString(
                    "O"
                )
            ?? "unknown";

        return (
            "Website Tracking: "
            + $"browser={browser}; "
            + $"domain={domain}; "
            + $"observed_at={observedAt}; "
            + $"accepted={snapshot.AcceptedCount}; "
            + $"rejected={snapshot.RejectedCount}"
        );
    }
}