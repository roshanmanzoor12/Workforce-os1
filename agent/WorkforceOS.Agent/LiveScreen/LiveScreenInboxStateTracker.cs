namespace WorkforceOS.Agent.LiveScreen;

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
