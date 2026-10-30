using System.IO.Pipes;
using System.Text;

namespace WorkforceOS.Agent.LiveScreen;

/// <summary>
/// Best-effort notification only. Never conveys device credentials, approves a session,
/// or instructs the companion to capture. The receiver must not treat pipe input as authorization.
/// </summary>
public static class CompanionRequestNotifier
{
    public const string PipeName = "WorkforceOS.ScreenCompanion.Requests.v1";

    public static async Task<bool> TryNotifyAsync(Guid sessionId, DateTimeOffset expiresAt, CancellationToken cancellationToken)
    {
        if (sessionId == Guid.Empty || expiresAt <= DateTimeOffset.UtcNow) return false;
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.Out, PipeOptions.Asynchronous);
            using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            timeout.CancelAfter(TimeSpan.FromMilliseconds(600));
            await pipe.ConnectAsync(timeout.Token);
            var line = $"{sessionId:D}|{expiresAt.ToUnixTimeSeconds()}\n";
            var bytes = Encoding.ASCII.GetBytes(line);
            await pipe.WriteAsync(bytes, timeout.Token);
            await pipe.FlushAsync(timeout.Token);
            return true;
        }
        catch (Exception ex) when (ex is IOException or TimeoutException or OperationCanceledException or UnauthorizedAccessException)
        {
            return false;
        }
    }
}
