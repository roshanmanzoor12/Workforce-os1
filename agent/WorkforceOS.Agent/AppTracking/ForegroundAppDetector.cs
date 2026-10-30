using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

namespace WorkforceOS.Agent.AppTracking;

public sealed class ForegroundAppDetector
{
    private readonly ILogger<ForegroundAppDetector> _logger;

    public ForegroundAppDetector(
        ILogger<ForegroundAppDetector> logger)
    {
        _logger = logger;
    }

    public ForegroundAppSnapshot? GetForegroundApplication(
        bool captureWindowTitle)
    {
        IntPtr windowHandle =
            GetForegroundWindow();

        if (windowHandle == IntPtr.Zero)
        {
            return null;
        }

        _ = GetWindowThreadProcessId(
            windowHandle,
            out uint processId);

        if (processId == 0)
        {
            return null;
        }

        try
        {
            using Process process =
                Process.GetProcessById(
                    checked((int)processId));

            string processName =
                NormalizeProcessName(
                    process.ProcessName);

            string? executablePath =
                TryGetExecutablePath(
                    process);

            string? windowTitle =
                captureWindowTitle
                    ? GetWindowTitle(
                        windowHandle)
                    : null;

            return new ForegroundAppSnapshot
            {
                ProcessName = processName,
                ExecutablePath = executablePath,
                WindowTitle = windowTitle,
                ObservedAt =
                    DateTimeOffset.UtcNow,
                ProcessId =
                    checked((int)processId),
            };
        }
        catch (
            ArgumentException exception)
        {
            _logger.LogDebug(
                exception,
                "Foreground process {ProcessId} exited before inspection.",
                processId);

            return null;
        }
        catch (
            InvalidOperationException exception)
        {
            _logger.LogDebug(
                exception,
                "Unable to inspect foreground process {ProcessId}.",
                processId);

            return null;
        }
    }

    private static string NormalizeProcessName(
        string processName)
    {
        string normalized =
            processName.Trim();

        if (normalized.EndsWith(
            ".exe",
            StringComparison.OrdinalIgnoreCase))
        {
            return normalized;
        }

        return normalized + ".exe";
    }

    private static string? TryGetExecutablePath(
        Process process)
    {
        try
        {
            string? fileName =
                process.MainModule?.FileName;

            if (string.IsNullOrWhiteSpace(
                fileName))
            {
                return null;
            }

            return fileName.Trim();
        }
        catch (
            System.ComponentModel.Win32Exception)
        {
            return null;
        }
        catch (
            InvalidOperationException)
        {
            return null;
        }
        catch (
            NotSupportedException)
        {
            return null;
        }
    }

    private static string? GetWindowTitle(
        IntPtr windowHandle)
    {
        int titleLength =
            GetWindowTextLength(
                windowHandle);

        if (titleLength <= 0)
        {
            return null;
        }

        const int maximumCharacters =
            2048;

        int capacity =
            Math.Min(
                titleLength + 1,
                maximumCharacters);

        StringBuilder builder =
            new(
                capacity);

        int charactersCopied =
            GetWindowText(
                windowHandle,
                builder,
                builder.Capacity);

        if (charactersCopied <= 0)
        {
            return null;
        }

        string result =
            builder
                .ToString()
                .Trim();

        return string.IsNullOrWhiteSpace(
            result)
            ? null
            : result;
    }

    [DllImport(
        "user32.dll")]
    private static extern IntPtr GetForegroundWindow();

    [DllImport(
        "user32.dll")]
    private static extern uint GetWindowThreadProcessId(
        IntPtr hWnd,
        out uint lpdwProcessId);

    [DllImport(
        "user32.dll",
        CharSet = CharSet.Unicode)]
    private static extern int GetWindowText(
        IntPtr hWnd,
        StringBuilder lpString,
        int nMaxCount);

    [DllImport(
        "user32.dll",
        CharSet = CharSet.Unicode)]
    private static extern int GetWindowTextLength(
        IntPtr hWnd);
}