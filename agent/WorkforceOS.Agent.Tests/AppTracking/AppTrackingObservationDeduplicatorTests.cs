using WorkforceOS.Agent.AppTracking;

namespace WorkforceOS.Agent.Tests.AppTracking;

public sealed class AppTrackingObservationDeduplicatorTests
{
    [Fact]
    public void FirstObservation_IsAccepted()
    {
        AppTrackingObservationDeduplicator deduplicator =
            new();

        AppTrackingSessionObservation observation =
            Create(
                "code.exe",
                DateTimeOffset.UtcNow);

        Assert.True(
            deduplicator.ShouldAccept(
                observation));
    }

    [Fact]
    public void OlderObservation_IsRejected()
    {
        AppTrackingObservationDeduplicator deduplicator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        Assert.True(
            deduplicator.ShouldAccept(
                Create(
                    "code.exe",
                    now)));

        Assert.False(
            deduplicator.ShouldAccept(
                Create(
                    "chrome.exe",
                    now.AddSeconds(
                        -1))));
    }

    [Fact]
    public void NewerObservation_IsAccepted()
    {
        AppTrackingObservationDeduplicator deduplicator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        Assert.True(
            deduplicator.ShouldAccept(
                Create(
                    "code.exe",
                    now)));

        Assert.True(
            deduplicator.ShouldAccept(
                Create(
                    "chrome.exe",
                    now.AddSeconds(
                        1))));
    }

    [Fact]
    public void Reset_AllowsFreshObservation()
    {
        AppTrackingObservationDeduplicator deduplicator =
            new();

        DateTimeOffset now =
            DateTimeOffset.UtcNow;

        Assert.True(
            deduplicator.ShouldAccept(
                Create(
                    "code.exe",
                    now)));

        deduplicator.Reset();

        Assert.True(
            deduplicator.ShouldAccept(
                Create(
                    "code.exe",
                    now)));
    }

    private static AppTrackingSessionObservation Create(
        string processName,
        DateTimeOffset observedAt)
    {
        return new AppTrackingSessionObservation
        {
            SessionId = 1,

            UserSid =
                "S-1-5-21-1000-1000-1000-1001",

            ProcessName =
                processName,

            ExecutablePath =
                $@"C:\Apps\{processName}",

            WindowTitle =
                null,

            ObservedAt =
                observedAt,
        };
    }
}