using System.Threading;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Manages an employee-visible live sharing session, but does not capture any pixels.
/// A production transport must enforce device identity and server-issued session grants.
/// Call ReconcileAsync on every authorization/shift change, and StopAsync on shutdown.
/// </summary>
public sealed class LiveScreenSessionCoordinator : IAsyncDisposable
{
    private readonly ILiveScreenSessionTransport _transport;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private bool _running;
    private bool _disposed;
    private Guid _employeeId;
    private Guid _deviceId;
    private Guid _workspaceId;
    private Guid _sessionId;

    public LiveScreenSessionCoordinator(ILiveScreenSessionTransport transport)
    {
        _transport = transport ?? throw new ArgumentNullException(nameof(transport));
    }

    public async Task<LiveScreenDecision> ReconcileAsync(
        LiveScreenContext context, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(context);
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            ObjectDisposedException.ThrowIf(_disposed, this);
            var decision = LiveScreenEligibility.Evaluate(context);
            if (!decision.CanShare)
            {
                await StopInternalAsync(cancellationToken).ConfigureAwait(false);
                return decision;
            }

            if (_running && _employeeId == context.EmployeeId &&
                _deviceId == context.DeviceId && _workspaceId == context.WorkspaceId &&
                _sessionId == context.SessionId)
                return decision; // Already active; do not duplicate a session.

            await StopInternalAsync(cancellationToken).ConfigureAwait(false);
            await _transport.StartAsync(context, cancellationToken).ConfigureAwait(false);
            _running = true;
            _employeeId = context.EmployeeId;
            _deviceId = context.DeviceId;
            _workspaceId = context.WorkspaceId;
            _sessionId = context.SessionId;
            return decision;
        }
        finally { _gate.Release(); }
    }

    public async Task StopAsync(CancellationToken cancellationToken = default)
    {
        await _gate.WaitAsync(cancellationToken).ConfigureAwait(false);
        try
        {
            if (_disposed) return;
            await StopInternalAsync(cancellationToken).ConfigureAwait(false);
        }
        finally { _gate.Release(); }
    }

    private async Task StopInternalAsync(CancellationToken cancellationToken)
    {
        if (!_running) return;
        // Fail closed: clear local state even if the downstream stop fails.
        _running = false;
        _employeeId = _deviceId = _workspaceId = _sessionId = Guid.Empty;
        await _transport.StopAsync(cancellationToken).ConfigureAwait(false);
    }

    public async ValueTask DisposeAsync()
    {
        await _gate.WaitAsync().ConfigureAwait(false);
        try
        {
            if (_disposed) return;
            try { await StopInternalAsync(CancellationToken.None).ConfigureAwait(false); }
            finally { _disposed = true; }
        }
        finally { _gate.Release(); }
        // Semaphore not disposed: allows harmless late cancellation/cleanup attempts.
    }
}

public interface ILiveScreenSessionTransport
{
    Task StartAsync(LiveScreenContext context, CancellationToken cancellationToken);
    Task StopAsync(CancellationToken cancellationToken);
}
