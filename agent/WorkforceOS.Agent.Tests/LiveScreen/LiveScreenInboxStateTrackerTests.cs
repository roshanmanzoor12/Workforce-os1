using WorkforceOS.Agent.LiveScreen;

namespace WorkforceOS.Agent.Tests.LiveScreen;

public sealed class LiveScreenInboxStateTrackerTests
{
    private static LiveScreenInboxResponse Inbox(DateTimeOffset expiry, params Guid[] ids) => new()
    {
        CaptureAuthorized = false,
        Sessions = ids.Select(id => new LiveScreenInboxItem
        {
            SessionId = id, Status = "requested", ExpiresAt = expiry,
            ConsentRequired = true, VisibleIndicatorRequired = true
        }).ToList()
    };

    [Fact]
    public void FirstEmptyReadReportsConnectionOnce()
    {
        var tracker = new LiveScreenInboxStateTracker();
        var now = DateTimeOffset.UtcNow;
        Assert.True(tracker.Observe(Inbox(now.AddMinutes(1)), now).Changed);
        Assert.False(tracker.Observe(Inbox(now.AddMinutes(1)), now).Changed);
    }

    [Fact]
    public void DuplicateSessionDoesNotGenerateRepeatedChanges()
    {
        var tracker = new LiveScreenInboxStateTracker();
        var now = DateTimeOffset.UtcNow;
        var id = Guid.NewGuid();
        Assert.Equal(1, tracker.Observe(Inbox(now.AddMinutes(1), id), now).AddedCount);
        Assert.False(tracker.Observe(Inbox(now.AddMinutes(1), id), now).Changed);
    }

    [Fact]
    public void ExpiredSessionIsNotCounted()
    {
        var tracker = new LiveScreenInboxStateTracker();
        var now = DateTimeOffset.UtcNow;
        Assert.Equal(0, tracker.Observe(Inbox(now.AddSeconds(-1), Guid.NewGuid()), now).CurrentCount);
    }

    [Fact]
    public void DisappearanceProducesRemoval()
    {
        var tracker = new LiveScreenInboxStateTracker();
        var now = DateTimeOffset.UtcNow;
        tracker.Observe(Inbox(now.AddMinutes(1), Guid.NewGuid()), now);
        var change = tracker.Observe(Inbox(now.AddMinutes(1)), now);
        Assert.True(change.Changed);
        Assert.Equal(1, change.RemovedCount);
    }

    [Fact]
    public void ConnectionFailureInvalidatesStaleStateAndOnlyLogsOnce()
    {
        var tracker = new LiveScreenInboxStateTracker();
        var now = DateTimeOffset.UtcNow;
        tracker.Observe(Inbox(now.AddMinutes(1), Guid.NewGuid()), now);
        Assert.True(tracker.MarkUnavailable());
        Assert.False(tracker.MarkUnavailable());
        var recovered = tracker.Observe(Inbox(now.AddMinutes(1)), now);
        Assert.True(recovered.Changed);
        Assert.Equal(0, recovered.CurrentCount);
    }
}
