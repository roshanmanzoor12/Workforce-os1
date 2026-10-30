using System.Drawing;
using System.Windows.Forms;

namespace WorkforceOS.ScreenCompanion;

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
    private bool _sharing;

    public SharingWindow()
    {
        Text = "WorkforceOS — Employee Screen Sharing";
        Width = 940;
        Height = 690;
        MinimumSize = new Size(640, 480);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.Sizable;

        _status.Text = "Screen sharing is OFF — no desktop frames are captured";
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
        _tray.DoubleClick += (_, _) => { Show(); WindowState = FormWindowState.Normal; Activate(); };
        var menu = new ContextMenuStrip();
        menu.Items.Add("Open WorkforceOS sharing", null, (_, _) => { Show(); Activate(); });
        menu.Items.Add("Stop sharing", null, (_, _) => StopPreview());
        menu.Items.Add("Exit", null, (_, _) => Close());
        _tray.ContextMenuStrip = menu;
    }

    private void StartPreview()
    {
        if (_sharing) return;
        var answer = MessageBox.Show(
            "Start employee-visible LOCAL desktop preview? This milestone does NOT transmit frames to the owner or backend. You can stop any time.",
            "Authorize screen preview", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
        if (answer != DialogResult.Yes) return;
        _sharing = true;
        _status.Text = "● SCREEN PREVIEW ACTIVE — STOP SHARING to end capture";
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
        _status.Text = "Screen sharing is OFF — no desktop frames are captured";
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
        _timer.Dispose();
        base.OnFormClosing(e);
    }
}
