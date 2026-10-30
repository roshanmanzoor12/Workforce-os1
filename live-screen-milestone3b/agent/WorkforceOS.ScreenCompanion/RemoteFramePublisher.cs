using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net.WebSockets;
using System.Threading;
using System.Threading.Tasks;

namespace WorkforceOS.ScreenCompanion;

// Connects only while the employee has explicitly started sharing.
internal sealed class RemoteFramePublisher : IDisposable
{
    private ClientWebSocket? _socket;
    private readonly SemaphoreSlim _gate = new(1, 1);
    private readonly string _url;
    public bool Connected => _socket?.State == WebSocketState.Open;

    public RemoteFramePublisher(string url) { _url = url; }

    public async Task SendAsync(Image source)
    {
        if (!await _gate.WaitAsync(0)) return; // Drop frames rather than accumulate screen data.
        try
        {
            if (_socket?.State != WebSocketState.Open)
            {
                _socket?.Dispose();
                _socket = new ClientWebSocket();
                using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(3));
                await _socket.ConnectAsync(new Uri(_url), timeout.Token);
            }
            using var stream = new MemoryStream();
            using (var small = new Bitmap(source, new Size(Math.Min(1024, source.Width), Math.Max(1, source.Height * Math.Min(1024, source.Width) / source.Width))))
                small.Save(stream, ImageFormat.Jpeg);
            if (stream.Length > 900_000) return;
            await _socket.SendAsync(new ArraySegment<byte>(stream.ToArray()), WebSocketMessageType.Binary, true, CancellationToken.None);
        }
        catch (Exception) { _socket?.Dispose(); _socket = null; }
        finally { _gate.Release(); }
    }

    public void Stop()
    {
        _socket?.Abort();
        _socket?.Dispose();
        _socket = null;
    }
    public void Dispose() { Stop(); _gate.Dispose(); }
}
