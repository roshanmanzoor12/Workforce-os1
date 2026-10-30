using System.Drawing;
using System.Drawing.Imaging;
using System.Net.Http.Headers;

namespace WorkforceOS.ScreenCompanion;

// Publishes only an employee-approved, backend-activated session.
internal sealed class RemoteFramePublisher : IDisposable
{
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromSeconds(12) };
    private readonly string _apiBase;
    private readonly string _deviceUuid;
    private readonly string _deviceSecret;
    private readonly Guid _sessionId;
    private readonly Action<Guid>? _onTerminal;
    private readonly CancellationTokenSource _stop = new();
    private readonly SemaphoreSlim _gate = new(1, 1);
    private readonly string _logPath;
    private int _stopped;
    private int _consecutiveFailures;
    private long _retryAfterUtcTicks;

    public RemoteFramePublisher(string apiBase, Guid sessionId, string deviceUuid, string deviceSecret, Action<Guid>? onTerminal = null)
    {
        _apiBase = apiBase.TrimEnd('/');
        _sessionId = sessionId;
        _onTerminal = onTerminal;
        _deviceUuid = deviceUuid;
        _deviceSecret = deviceSecret;
        var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "WorkforceOS", "logs");
        Directory.CreateDirectory(dir);
        _logPath = Path.Combine(dir, "screen-companion.log");
        Log($"publisher started session={sessionId:D} api={_apiBase}");
    }

    public bool IsRunning => Volatile.Read(ref _stopped) == 0;

    public async Task SendAsync(Image source)
    {
        if (Volatile.Read(ref _stopped) != 0 || DateTime.UtcNow.Ticks < Interlocked.Read(ref _retryAfterUtcTicks) || !_gate.Wait(0)) return;
        try
        {
            var jpeg = Encode(source);
            if (jpeg is null || _stop.IsCancellationRequested) return;
            using var request = new HttpRequestMessage(HttpMethod.Post, $"{_apiBase}/api/v1/device-agent/live-screen/{_sessionId:D}/native-frame");
            request.Headers.TryAddWithoutValidation("X-Device-UUID", _deviceUuid);
            request.Headers.TryAddWithoutValidation("X-Device-Secret", _deviceSecret);
            request.Content = new ByteArrayContent(jpeg);
            request.Content.Headers.ContentType = new MediaTypeHeaderValue("image/jpeg");
            using var response = await _http.SendAsync(request, _stop.Token);
            if (response.IsSuccessStatusCode)
            {
                Interlocked.Exchange(ref _consecutiveFailures, 0);
                Interlocked.Exchange(ref _retryAfterUtcTicks, 0);
                return;
            }
            var body = await response.Content.ReadAsStringAsync(_stop.Token);
            var failures = Interlocked.Increment(ref _consecutiveFailures);
            Log($"frame upload failed status={(int)response.StatusCode} {response.ReasonPhrase} bytes={jpeg.Length} consecutive={failures} body={Trim(body)}");
            // Pending employee approval is recoverable. The server remains the sole
            // authority for frame authorization; no frame is accepted until active.
            // Back off rather than flooding the API while approval is pending.
            if ((int)response.StatusCode == 403 &&
                body.Contains("Active employee-approved session required", StringComparison.OrdinalIgnoreCase))
            {
                Interlocked.Exchange(ref _retryAfterUtcTicks, DateTime.UtcNow.AddSeconds(5).Ticks);
                return;
            }
            // Credential failures, non-pending 403 and missing sessions remain terminal.
            if ((int)response.StatusCode is 401 or 403 or 404 or 410)
            {
                Stop();
                _onTerminal?.Invoke(_sessionId); // notify UI to stop local capture too
            }
            // 409 can be a transient relay contention; retry with a bounded delay.
            if ((int)response.StatusCode == 409)
                Interlocked.Exchange(ref _retryAfterUtcTicks, DateTime.UtcNow.AddSeconds(5).Ticks);
        }
        catch (OperationCanceledException) when (_stop.IsCancellationRequested) { }
        catch (Exception ex)
        {
            var failures = Interlocked.Increment(ref _consecutiveFailures);
            Log($"frame upload exception consecutive={failures} {ex.GetType().Name}: {ex.Message}");
            // Temporary backend disconnects/timeouts must not permanently stop the publisher.
            // The backend still authorizes every upload; explicit Stop() remains terminal.
            // The next frame callback retries after the backend recovers.
        }
        finally { _gate.Release(); }
    }

    private static byte[]? Encode(Image source)
    {
        foreach (var width in new[] { 1280, 1024, 800 })
        {
            var height = Math.Max(1, (int)Math.Round(source.Height * (double)Math.Min(width, source.Width) / source.Width));
            using var small = new Bitmap(source, new Size(Math.Min(width, source.Width), height));
            using var stream = new MemoryStream();
            var codec = ImageCodecInfo.GetImageEncoders().FirstOrDefault(c => c.MimeType == "image/jpeg");
            if (codec is null) return null;
            using var quality = new EncoderParameters(1);
            quality.Param[0] = new EncoderParameter(System.Drawing.Imaging.Encoder.Quality, 60L);
            small.Save(stream, codec, quality);
            if (stream.Length <= 850_000) return stream.ToArray();
        }
        return null;
    }

    private void Log(string message)
    {
        try { File.AppendAllText(_logPath, $"{DateTimeOffset.Now:O} {message}{Environment.NewLine}"); } catch { }
    }
    private static string Trim(string value) => value.Length > 300 ? value[..300] : value;

    public void Stop()
    {
        if (Interlocked.Exchange(ref _stopped, 1) != 0) return;
        Log($"publisher stopped session={_sessionId:D}");
        _stop.Cancel();
        _http.Dispose();
    }

    public void Dispose() { Stop(); _gate.Dispose(); _stop.Dispose(); }
}
