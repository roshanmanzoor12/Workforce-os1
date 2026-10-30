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
    protected override void SetVisibleCore(bool value)
    {
        if (value && !_allowDisplay) value = false;
        base.SetVisibleCore(value);
    }
    private void OpenControls()
    {
        _allowDisplay = true;
        ShowInTaskbar = true;
        Show();
        WindowState = FormWindowState.Normal;
        Activate();
    }
    private bool _sharing;
    // WFOS_3B_NATIVE_PUBLISHER: sender exists only while employee-authorized sharing is active.
    private RemoteFramePublisher? _publisher;
    private readonly string _remoteUrl = Environment.GetEnvironmentVariable("WFOS_SCREEN_SEND_URL") ?? "";

    public SharingWindow()
    {
        CompanionDiagnostics.Log("companion process started");
        _uiContext = SynchronizationContext.Current ?? new WindowsFormsSynchronizationContext();
        Text = "WorkforceOS â€” Employee Screen Sharing";
        Width = 940;
        Height = 690;
        MinimumSize = new Size(640, 480);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.Sizable;

        _status.Text = "Screen sharing is OFF â€” no desktop frames are captured";
        _status.AutoSize = false;
        _status.Height = 35;
        _status.Dock = DockStyle.Top;
        _status.TextAlign = ContentAlignment.MiddleCenter;
        _status.Font = new Font(Font.FontFamily, 11, FontStyle.Bold);

        var controlRow = new FlowLayoutPanel { Dock = DockStyle.Top, Height = 50, Padding = new Padding(12, 6, 0, 0) };
        _start.Text = "Start local preview (consent)";
        _start.Width = 230;
        _start.Height = 32;
        _start.Click += (_, _) => StartPreview();
        _stop.Text = "STOP SHARING";
        _stop.Width = 180;
        _stop.Height = 32;
        _stop.Enabled = false;
        _stop.Click += (_, _) => StopPreview();
        controlRow.Controls.Add(_start);
        controlRow.Controls.Add(_stop);

        _preview.Dock = DockStyle.Fill;
        _preview.SizeMode = PictureBoxSizeMode.Zoom;
        _preview.BackColor = Color.FromArgb(20, 23, 29);
        Controls.Add(_preview);
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
                    OpenControls();
                    var answer = MessageBox.Show(this,
                        $"Workspace owner requests viewing your desktop.\n\nSession: {sessionId:D}\nExpires: {expiresAt.LocalDateTime:g}\n\nAccepting starts a visible screen-sharing session. You can stop it anytime.",
                        "WorkforceOS - Native Screen Request", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
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
        });
    }

    private void StartRemoteSession(Guid sessionId, string apiBase, string deviceUuid, string deviceSecret)
    {
        CompanionDiagnostics.Log($"start command received session={sessionId:D} api={apiBase}");
        if (_sharing) StopPreview();
        _publisher?.Dispose();
        _publisher = new RemoteFramePublisher(apiBase, sessionId, deviceUuid, deviceSecret);
        _sharing = true;
        _status.Text = "● SCREEN SHARING ACTIVE — STOP SHARING to end capture";
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
        _status.Text = "â— SCREEN PREVIEW ACTIVE â€” STOP SHARING to end capture";
        _status.ForeColor = Color.DarkRed;
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
            var old = _preview.Image;
            _preview.Image = (Image)bitmap.Clone();
            old?.Dispose();
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
        _timer.Stop();
        _sharing = false;
        _publisher?.Stop();
        _publisher = null;
        _status.Text = "Screen sharing is OFF â€” no desktop frames are captured";
        _status.ForeColor = SystemColors.ControlText;
        _tray.Text = "WorkforceOS sharing is OFF";
        _start.Enabled = true;
        _stop.Enabled = false;
        var old = _preview.Image;
        _preview.Image = null;
        old?.Dispose();
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



