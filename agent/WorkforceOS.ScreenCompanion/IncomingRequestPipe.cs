using System.IO.Pipes;
using System.Text;

namespace WorkforceOS.ScreenCompanion;

internal sealed class IncomingRequestPipe : IDisposable
{
    private const string PipeName = "WorkforceOS.ScreenCompanion.Requests.v1";
    private readonly CancellationTokenSource _shutdown = new();
    private readonly Func<Guid, DateTimeOffset, Task<string>> _received;
    private readonly Func<Guid, string, string, string, CancellationToken, Task>? _start;
    private readonly Func<Guid, Task<bool>>? _prepare;

    public IncomingRequestPipe(Func<Guid, DateTimeOffset, Task<string>> received,
        Func<Guid, string, string, string, CancellationToken, Task>? start = null,
        Func<Guid, Task<bool>>? prepare = null)
    {
        _received = received;
        _start = start;
        _prepare = prepare;
        _ = ListenAsync(_shutdown.Token);
    }

    private async Task ListenAsync(CancellationToken stop)
    {
        while (!stop.IsCancellationRequested)
        {
            try
            {
                using var server = new NamedPipeServerStream(PipeName, PipeDirection.InOut, 1, PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
                await server.WaitForConnectionAsync(stop);
                CompanionDiagnostics.Log("named pipe client connected");
                using var reader = new StreamReader(server, Encoding.UTF8, false, 2048, leaveOpen: true);
                var raw = await reader.ReadLineAsync(stop);
                if (string.IsNullOrWhiteSpace(raw) || raw.Length > 4096) continue;
                var parts = raw.Split('|');
                if (parts.Length == 2 && parts[0] == "prepare" &&
                    Guid.TryParse(parts[1], out var prepareId) && prepareId != Guid.Empty && _prepare is not null)
                {
                    var ready = await _prepare(prepareId);
                    await server.WriteAsync(Encoding.UTF8.GetBytes(ready ? "ready\n" : "unavailable\n"), stop);
                    await server.FlushAsync(stop);
                    continue;
                }
                if (parts.Length == 5 && parts[0] == "start" && Guid.TryParse(parts[1], out var sid) && sid != Guid.Empty && _start is not null)
                {
                    CompanionDiagnostics.Log($"named pipe start received session={sid:D}");
                    await _start(sid, parts[2], parts[3], parts[4], stop);
                    await server.WriteAsync(Encoding.UTF8.GetBytes("ok\n"), stop);
                    await server.FlushAsync(stop);
                    continue;
                }
                if (parts.Length != 2 || !Guid.TryParse(parts[0], out var id) || id == Guid.Empty || !long.TryParse(parts[1], out var expiryUnix)) continue;
                DateTimeOffset expiry;
                try { expiry = DateTimeOffset.FromUnixTimeSeconds(expiryUnix); } catch (ArgumentOutOfRangeException) { continue; }
                if (expiry <= DateTimeOffset.UtcNow || expiry > DateTimeOffset.UtcNow.AddHours(24)) continue;
                var decision = await _received(id, expiry);
                await server.WriteAsync(Encoding.UTF8.GetBytes((decision is "accept" or "decline" ? decision : "decline") + "\n"), stop);
                await server.FlushAsync(stop);
            }
            catch (OperationCanceledException) when (stop.IsCancellationRequested) { break; }
            catch (IOException) { }
            catch (Exception) when (!stop.IsCancellationRequested) { try { await Task.Delay(500, stop); } catch { break; } }
        }
    }
    public void Dispose() => _shutdown.Cancel();
}
