#!/usr/bin/env python3
"""Add read-only inbox state-change diagnostics to WorkforceOS.Agent.
Does not authorize capture, initiate screen sharing, or handle media.
"""
from pathlib import Path
from datetime import datetime
import shutil, sys

TRACKER = r'''namespace WorkforceOS.Agent.LiveScreen;

/// <summary>Read-only inbox diagnostics. Retains no device secrets or media.</summary>
public sealed class LiveScreenInboxStateTracker
{
    private HashSet<Guid> _current = new();
    private bool _hasSuccessfulRead;
    private bool _offline;

    public LiveScreenInboxChange Observe(LiveScreenInboxResponse inbox, DateTimeOffset now)
    {
        if (!LiveScreenInboxClient.IsValid(inbox))
            throw new InvalidDataException("Invalid inbox data.");

        // Expired inbox items must not be surfaced to the operator.
        var active = inbox.Sessions.Where(s => s.ExpiresAt > now)
            .Select(s => s.SessionId).ToHashSet();
        var added = active.Except(_current).Count();
        var removed = _current.Except(active).Count();
        var changed = !_hasSuccessfulRead || added != 0 || removed != 0 || _offline;
        _current = active;
        _hasSuccessfulRead = true;
        _offline = false;
        return new LiveScreenInboxChange(changed, active.Count, added, removed, false);
    }

    public bool MarkUnavailable()
    {
        if (_offline) return false;
        _offline = true;
        // Do not display stale inbox items as currently available.
        _current.Clear();
        return true;
    }
}

public sealed record LiveScreenInboxChange(
    bool Changed, int CurrentCount, int AddedCount, int RemovedCount, bool CaptureAuthorized);
'''

TEST = r'''using WorkforceOS.Agent.LiveScreen;

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
'''

OLD = '''                    // Read-only visibility: no session activation and no capture.
                    if (inbox.Sessions.Count > 0)
                    {
                        _logger.LogInformation(
                            "Live-screen inbox contains {Count} request(s); capture is not enabled by inbox responses.",
                            inbox.Sessions.Count);
                    }'''
NEW = '''                    // Read-only visibility: never activate/capture from inbox data.
                    var change = tracker.Observe(inbox, DateTimeOffset.UtcNow);
                    if (change.Changed)
                    {
                        _logger.LogInformation(
                            "Live-screen inbox connected: {Count} valid request(s), {Added} new, {Removed} removed. Media transport not configured.",
                            change.CurrentCount, change.AddedCount, change.RemovedCount);
                    }'''

def main():
    root=Path(sys.argv[1] if len(sys.argv)>1 else r'C:\workforce-os')
    base=root/'agent/WorkforceOS.Agent/LiveScreen'
    worker=base/'LiveScreenInboxWorker.cs'
    state=base/'LiveScreenInboxStateTracker.cs'
    test=root/'agent/WorkforceOS.Agent.Tests/LiveScreen/LiveScreenInboxStateTrackerTests.cs'
    if not worker.is_file(): raise SystemExit(f'Missing {worker}')
    src=worker.read_text(encoding='utf-8-sig')
    if 'var tracker = new LiveScreenInboxStateTracker();' in src:
        print('ALREADY INSTALLED');return
    if src.count(OLD)!=1 or src.count('        while (!stoppingToken.IsCancellationRequested)')!=1 or src.count('            catch (Exception ex)')!=1:
        raise SystemExit('Agent worker differs from expected version; no changes applied.')
    if state.exists() or test.exists():raise SystemExit('Target diagnostics file already exists; no changes applied.')
    modified=src.replace('        while (!stoppingToken.IsCancellationRequested)', '        var tracker = new LiveScreenInboxStateTracker();\n        while (!stoppingToken.IsCancellationRequested)',1).replace(OLD,NEW,1).replace('''                // Never log credentials or response payloads.
                _logger.LogWarning("Live-screen inbox unavailable ({ErrorType}); retrying.",
                    ex.GetType().Name);''','''                // Do not log credentials, response payloads, or repeated outages.
                if (tracker.MarkUnavailable())
                    _logger.LogWarning("Live-screen inbox unavailable ({ErrorType}); retrying.", ex.GetType().Name);''',1)
    if modified==src or 'tracker.MarkUnavailable()' not in modified:raise SystemExit('Patch anchors missing.')
    backup=root/'backups'/('agent-inbox-diagnostics-'+datetime.now().strftime('%Y%m%d-%H%M%S'))/'agent/WorkforceOS.Agent/LiveScreen/LiveScreenInboxWorker.cs'
    backup.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(worker,backup)
    try:
        state.write_text(TRACKER,encoding='utf-8')
        test.parent.mkdir(parents=True,exist_ok=True)
        test.write_text(TEST,encoding='utf-8')
        worker.write_text(modified,encoding='utf-8')
    except Exception:
        shutil.copy2(backup,worker)
        state.unlink(missing_ok=True)
        test.unlink(missing_ok=True)
        raise
    print('PATCHED',worker)
    print('ADDED',state)
    print('ADDED',test)
    print('BACKUP',backup)
    print('NOTE: Adds operational inbox status only; capture authorization remains false. No video transport.')

if __name__=='__main__':main()
