using System.IO.Pipes;
using System.Text;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>Local, informational request/decision channel. This does NOT authorize capture.</summary>
public static class CompanionRequestNotifier
{
    public const string PipeName = "WorkforceOS.ScreenCompanion.Requests.v1";

    public static async Task<string?> RequestDecisionAsync(Guid sessionId, DateTimeOffset expiresAt, CancellationToken cancellationToken)
    {
        if (sessionId == Guid.Empty || expiresAt <= DateTimeOffset.UtcNow) return null;
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(60));
            await pipe.ConnectAsync(timeout.Token);
            var bytes = Encoding.ASCII.GetBytes($"{sessionId:D}|{expiresAt.ToUnixTimeSeconds()}\n");
            await pipe.WriteAsync(bytes, timeout.Token);
            await pipe.FlushAsync(timeout.Token);
            using var reader = new StreamReader(pipe, Encoding.ASCII, false, 256, leaveOpen: true);
            var response = await reader.ReadLineAsync(timeout.Token);
            return response is "accept" or "decline" ? response : null;
        }
        catch (Exception ex) when (ex is IOException or TimeoutException or OperationCanceledException or UnauthorizedAccessException)
        {
            return null;
        }
    }
    public static async Task<bool> PrepareIndicatorAsync(Guid sessionId, CancellationToken cancellationToken)
    {
        if (sessionId == Guid.Empty) return false;
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(8));
            await pipe.ConnectAsync(timeout.Token);
            await pipe.WriteAsync(Encoding.UTF8.GetBytes($"prepare|{sessionId:D}\n"), timeout.Token);
            await pipe.FlushAsync(timeout.Token);
            using var reader = new StreamReader(pipe, Encoding.UTF8, false, 256, leaveOpen: true);
            return await reader.ReadLineAsync(timeout.Token) == "ready";
        }
        catch (Exception ex) when (ex is IOException or TimeoutException or OperationCanceledException or UnauthorizedAccessException)
        {
            return false; // fail closed; the employee popup will be used instead.
        }
    }

    public static async Task<bool> StartCaptureAsync(
        Guid sessionId, string apiBase, DeviceCredentials credentials,
        CancellationToken cancellationToken)
    {
        if (sessionId == Guid.Empty || !credentials.IsValid() || string.IsNullOrWhiteSpace(apiBase)) return false;
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut, PipeOptions.Asynchronous);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromSeconds(10));
            await pipe.ConnectAsync(timeout.Token);
            var line = $"start|{sessionId:D}|{apiBase.TrimEnd('/')}|{credentials.DeviceUuid:D}|{credentials.DeviceSecret}\n";
            await pipe.WriteAsync(Encoding.UTF8.GetBytes(line), timeout.Token);
            await pipe.FlushAsync(timeout.Token);
            using var reader = new StreamReader(pipe, Encoding.UTF8, false, 2048, leaveOpen: true);
            return (await reader.ReadLineAsync(timeout.Token)) == "ok";
        }
        catch (Exception ex) when (ex is IOException or TimeoutException or OperationCanceledException or UnauthorizedAccessException) { return false; }
    }

}
