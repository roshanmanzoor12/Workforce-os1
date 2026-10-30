using System.Drawing;
using System.Windows.Forms;

namespace WorkforceOS.ScreenCompanion;

internal static class CompanionDiagnostics
{
    private static readonly object Gate = new();
    private static readonly string PathName = System.IO.Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData),
        "WorkforceOS", "logs", "screen-companion.log");
    public static void Log(string message)
    {
        try
        {
            lock (Gate)
            {
                System.IO.Directory.CreateDirectory(System.IO.Path.GetDirectoryName(PathName)!);
                System.IO.File.AppendAllText(PathName, $"{DateTimeOffset.Now:O} {message}{Environment.NewLine}");
            }
        }
        catch { }
    }
}

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        ApplicationConfiguration.Initialize();
        Application.Run(new SharingWindow());
    }
}

internal sealed class SharingWindow : Form
{
    private readonly Label _status = new();
    private readonly Button _start = new();
    private readonly Button _stop = new();
    private readonly PictureBox _preview = new();
    private readonly System.Windows.Forms.Timer _timer = new();
    private readonly NotifyIcon _tray = new();
    private readonly IncomingRequestPipe _requestPipe;
    private readonly SynchronizationContext _uiContext;
    // WFOS_PHASE16_TRAY_START: no preview form on login; employee tray controls remain accessible.
    private bool _allowDisplay;
    // Keep the employee-visible bar unobtrusive without hiding sharing state.
    protected override bool ShowWithoutActivation => true;
    [System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
    private static extern bool SetWindowDisplayAffinity(IntPtr hwnd, uint affinity);
    protected override void SetVisibleCore(bool value)
    {
        // Native employee indicator is always hidden.
        base.SetVisibleCore(false);
    }
    private void OpenControls()
    {
        // Do not show the employee indicator window.
        _allowDisplay = false;

        if (Visible)
        {
            Hide();
        }
    }
    private bool _sharing;
    // WFOS_3B_NATIVE_PUBLISHER: sender exists only while employee-authorized sharing is active.
    private RemoteFramePublisher? _publisher;
    // WFOS_V9_EMPLOYEE_STOP_REVOCATION: credentials are never logged or displayed.
    private Guid _remoteSessionId;
    private string? _remoteApiBase;
    private string? _remoteDeviceUuid;
    private string? _remoteDeviceSecret;

    private readonly string _remoteUrl = Environment.GetEnvironmentVariable("WFOS_SCREEN_SEND_URL") ?? "";

    public SharingWindow()
    {
        CompanionDiagnostics.Log("companion process started");
        _uiContext = SynchronizationContext.Current ?? new WindowsFormsSynchronizationContext();
        Text = "WorkforceOS â€” Employee Screen Sharing";
        // WFOS_V18_MINI_SHARING_OVERLAY: employee-visible status + Stop Sharing.
        // No separate desktop preview. The authorized owner uses the web viewer.

        _status.Text = "Screen sharing is OFF â€” no desktop frames are captured";
        _status.AutoSize = false;
        _status.Height = 42;
        _status.Dock = DockStyle.Top;
        _status.TextAlign = ContentAlignment.MiddleCenter;
        _status.Font = new Font(Font.FontFamily, 10, FontStyle.Bold);

        var controlRow = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 50, Padding = new Padding(12, 6, 0, 0) };
        _start.Text = "Start local preview (consent)";
        _start.Width = 230;
        _start.Height = 32;
        _start.Click += (_, _) => StartPreview();
        _start.Visible = false;
        controlRow.Controls.Add(_stop);

        _preview.Dock = DockStyle.Fill;
        _preview.SizeMode = PictureBoxSizeMode.Zoom;
        _preview.BackColor = Color.FromArgb(20, 23, 29);
        // Never create a second desktop preview in the employee UI.
        Controls.Add(controlRow);
        Controls.Add(_status);

        _timer.Interval = 500;
        _timer.Tick += (_, _) => CaptureFrame();
        _tray.Icon = SystemIcons.Application;
        _tray.Text = "WorkforceOS sharing is OFF";
        _tray.Visible = true;
        _tray.DoubleClick += (_, _) => OpenControls();
        var menu = new ContextMenuStrip();
        menu.Items.Add("Open WorkforceOS sharing", null, (_, _) => OpenControls());
        menu.Items.Add("Stop sharing", null, (_, _) => StopPreview());
        menu.Items.Add("Exit", null, (_, _) => Close());
        _tray.ContextMenuStrip = menu;
        _requestPipe = new IncomingRequestPipe(async (sessionId, expiresAt) =>
        {
            if (IsDisposed) return "decline";
            var completion = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            try
            {
                _uiContext.Post(_ =>
                {
                    if (IsDisposed) { completion.TrySetResult("decline"); return; }
                    var answer = MessageBox.Show(
                        $"Workspace owner requests viewing your desktop.\n\nSession: {sessionId:D}\nExpires: {expiresAt.LocalDateTime:g}\n\nAccepting starts a screen-sharing session.",
                        "WorkforceOS - Native Screen Request",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question);

                    if (answer != DialogResult.Yes && !_sharing)
                    {
                        Hide();
                        _allowDisplay = false;
                    }
                    completion.TrySetResult(answer == DialogResult.Yes ? "accept" : "decline");
                }, null);
            }
            catch (Exception ex) { CompanionDiagnostics.Log($"request popup dispatch failed: {ex.Message}"); completion.TrySetResult("decline"); }
            return await completion.Task.WaitAsync(TimeSpan.FromSeconds(50));
        }, async (sessionId, apiBase, deviceUuid, deviceSecret, cancellationToken) =>
        {
            if (IsDisposed) { CompanionDiagnostics.Log("start command ignored disposed=true"); return; }
            try
            {
                CompanionDiagnostics.Log($"dispatching start command to UI session={sessionId:D}");
                _uiContext.Post(_ => StartRemoteSession(sessionId, apiBase, deviceUuid, deviceSecret), null);
                await Task.CompletedTask;
            }
            catch (Exception ex) { CompanionDiagnostics.Log($"start command dispatch failed: {ex.Message}"); }
        }, id => PrepareIndicatorAsync(id));
    }

    private Task<bool> PrepareIndicatorAsync(Guid sessionId)
    {
        var completion =
            new TaskCompletionSource<bool>(
                TaskCreationOptions.RunContinuationsAsynchronously);

        _uiContext.Post(_ =>
        {
            if (IsDisposed)
            {
                completion.TrySetResult(false);
                return;
            }

            // Report ready to the owner without displaying an indicator.
            completion.TrySetResult(true);
        }, null);

         return completion.Task.WaitAsync(TimeSpan.FromSeconds(6));
    }
    private void StartRemoteSession(Guid sessionId, string apiBase, string deviceUuid, string deviceSecret)
    {
        CompanionDiagnostics.Log($"start command received session={sessionId:D} api={apiBase}");
        if (_sharing && _remoteSessionId == sessionId)
        {
            if (_publisher?.IsRunning == true) return;
            _timer.Stop();
            _publisher?.Dispose();
            _publisher = null;
            _sharing = false;
            _remoteSessionId = Guid.Empty;
        }
        else if (_sharing) StopPreview();
        _publisher?.Dispose();
        _remoteSessionId = sessionId;
        _remoteApiBase = apiBase;
        _remoteDeviceUuid = deviceUuid;
        _remoteDeviceSecret = deviceSecret;
        _publisher = new RemoteFramePublisher(apiBase, sessionId, deviceUuid, deviceSecret,
            terminalId => _uiContext.Post(_ =>
            {
                if (!IsDisposed && _sharing && _remoteSessionId == terminalId) StopPreview();
            }, null));
        // A previous remote session may have hidden the bar in StopPreview().
        // Reopen it only after the replacement session is ready.
        OpenControls();
        _sharing = true;
        _status.ForeColor = Color.DarkRed;
        _tray.Text = "WorkforceOS screen sharing ACTIVE";
        _start.Enabled = false;
        _stop.Enabled = true;
        _timer.Start();
        CaptureFrame();
    }

    private void StartPreview(bool askForConsent = true)
    {
        if (_sharing) return;
        var answer = askForConsent ? MessageBox.Show(
            (_remoteUrl.Length > 0 ? "Start employee-visible REMOTE screen sharing to the configured WorkforceOS relay? Your screen will be transmitted to authorized viewers. STOP SHARING ends capture and transmission." : "Start employee-visible LOCAL desktop preview? No remote relay is configured. You can stop any time."),
            "Authorize screen preview", MessageBoxButtons.YesNo, MessageBoxIcon.Question) : DialogResult.Yes;
        if (answer != DialogResult.Yes) return;
        _sharing = true;
        // Manual local preview has no remote session; owner sessions use StartRemoteSession.
        _publisher = null;
        _tray.Text = "WorkforceOS LOCAL preview ACTIVE";
        _start.Enabled = false;
        _stop.Enabled = true;
        _timer.Start();
        CaptureFrame();
    }

    private void CaptureFrame()
    {
        if (!_sharing) return;
        try
        {
            var bounds = Screen.PrimaryScreen?.Bounds ?? throw new InvalidOperationException("No primary display found.");
            using var bitmap = new Bitmap(bounds.Width, bounds.Height);
            using (var graphics = Graphics.FromImage(bitmap))
                graphics.CopyFromScreen(bounds.Location, Point.Empty, bounds.Size);
            // No employee-side image rendering: publisher handles authorized frames.
            if (_publisher is not null)
            {
                // Bitmap clone survives CaptureFrame return; publishing never blocks UI thread.
                var remoteFrame = (Image)bitmap.Clone();
                var publisher = _publisher;
                _ = System.Threading.Tasks.Task.Run(async () =>
                {
                    try { if (publisher is not null) await publisher.SendAsync(remoteFrame); }
                    finally { remoteFrame.Dispose(); }
                });
            }
        }
        catch (Exception ex)
        {
            StopPreview();
            MessageBox.Show($"Desktop capture stopped: {ex.Message}", "Capture error", MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void StopPreview()
    {
        // Capture stops synchronously. Server revocation follows over authenticated HTTPS.
        var sessionId = _remoteSessionId;
        var apiBase = _remoteApiBase;
        var deviceUuid = _remoteDeviceUuid;
        var deviceSecret = _remoteDeviceSecret;
        _remoteSessionId = Guid.Empty;
        _remoteApiBase = null;
        _remoteDeviceUuid = null;
        _remoteDeviceSecret = null;
        if (sessionId != Guid.Empty && apiBase is not null &&
            deviceUuid is not null && deviceSecret is not null)
        {
            _ = RevokeRemoteSessionAsync(sessionId, apiBase, deviceUuid, deviceSecret);
        }
        _timer.Stop();
        _sharing = false;
        _publisher?.Stop();
        _publisher = null;
        _status.Text = "Screen sharing is OFF â€” no desktop frames are captured";
        _status.ForeColor = SystemColors.ControlText;
        _tray.Text = "WorkforceOS sharing is OFF";
        _start.Enabled = true;
        _stop.Enabled = false;
        // Idle: large app window stays hidden; employee can reopen controls in tray.
        Hide();
        _allowDisplay = false;
        var old = _preview.Image;
        _preview.Image = null;
        old?.Dispose();
    }

    private static async Task RevokeRemoteSessionAsync(
        Guid sessionId, string apiBase, string deviceUuid, string deviceSecret)
    {
        try
        {
            using var client = new HttpClient { Timeout = TimeSpan.FromSeconds(8) };
            using var request = new HttpRequestMessage(
                HttpMethod.Post,
                $"{apiBase.TrimEnd('/')}/api/v1/device-agent/live-screen/{sessionId:D}/stop");
            request.Headers.TryAddWithoutValidation("X-Device-UUID", deviceUuid);
            request.Headers.TryAddWithoutValidation("X-Device-Secret", deviceSecret);
            using var response = await client.SendAsync(request);
            CompanionDiagnostics.Log($"employee stop revocation session={sessionId:D} status={(int)response.StatusCode}");
        }
        catch (Exception ex)
        {
            CompanionDiagnostics.Log($"employee stop revocation retry needed session={sessionId:D} type={ex.GetType().Name}");
        }
    }

    protected override void OnFormClosing(FormClosingEventArgs e)
    {
        StopPreview();
        _tray.Visible = false;
        _tray.Dispose();
        _requestPipe.Dispose();
        _timer.Dispose();
        base.OnFormClosing(e);
    }
}



