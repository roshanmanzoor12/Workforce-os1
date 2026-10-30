using System.IO.Pipes;
using System.Text;

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
}
