using System.IO.Pipes;
using System.Text;

namespace WorkforceOS.ScreenCompanion;

/// <summary>
/// Informational local notification channel. Not an authorization or media channel.
/// Pipe messages never start capture; backend-approved session activation is separate.
/// </summary>
internal sealed class IncomingRequestPipe : IDisposable
{
    private const string PipeName = "WorkforceOS.ScreenCompanion.Requests.v1";
    private readonly CancellationTokenSource _shutdown = new();
    private readonly Action<Guid, DateTimeOffset> _received;

    public IncomingRequestPipe(Action<Guid, DateTimeOffset> received)
    {
        _received = received;
        _ = ListenAsync(_shutdown.Token);
    }

    private async Task ListenAsync(CancellationToken stop)
    {
        while (!stop.IsCancellationRequested)
        {
            try
            {
                using var server = new NamedPipeServerStream(PipeName, PipeDirection.In, 1,
                    PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
                await server.WaitForConnectionAsync(stop);
                using var reader = new StreamReader(server, Encoding.ASCII, false, 512, leaveOpen: true);
                var raw = await reader.ReadLineAsync(stop);
                if (raw is null || raw.Length > 120) continue;
                var parts = raw.Split('|');
                if (parts.Length != 2 || !Guid.TryParse(parts[0], out var id) || id == Guid.Empty ||
                    !long.TryParse(parts[1], out var expiryUnix)) continue;
                DateTimeOffset expiry;
                try { expiry = DateTimeOffset.FromUnixTimeSeconds(expiryUnix); }
                catch (ArgumentOutOfRangeException) { continue; }
                if (expiry <= DateTimeOffset.UtcNow || expiry > DateTimeOffset.UtcNow.AddHours(24)) continue;
                _received(id, expiry);
            }
            catch (OperationCanceledException) when (stop.IsCancellationRequested) { break; }
            catch (IOException) { /* Client disconnected; keep listening. */ }
            catch (Exception) when (!stop.IsCancellationRequested)
            {
                try { await Task.Delay(500, stop); }
                catch (OperationCanceledException) { break; }
            }
        }
    }

    public void Dispose() => _shutdown.Cancel();
}
