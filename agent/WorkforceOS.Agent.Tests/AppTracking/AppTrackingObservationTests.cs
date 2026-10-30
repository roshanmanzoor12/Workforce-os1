using WorkforceOS.Agent.AppTracking;

namespace WorkforceOS.Agent.Tests.AppTracking;

public sealed class AppTrackingObservationTests
{
    [Fact]
    public void FromSnapshot_SuppressesTitle_WhenDisabled()
    {
        ForegroundAppSnapshot snapshot =
            new()
            {
                ProcessName = "code.exe",
                ExecutablePath =
                    @"C:\Program Files\Microsoft VS Code\Code.exe",
                WindowTitle =
                    "secret-file.txt - Visual Studio Code",
                ObservedAt =
                    DateTimeOffset.UtcNow,
                ProcessId = 123,
            };

        AppTrackingOptions options =
            new()
            {
                Enabled = true,
                CaptureWindowTitles = false,
                MonitoringDisclosureRequired = true,
            };

        AppTrackingObservation result =
            AppTrackingObservation.FromSnapshot(
                snapshot,
                options);

        Assert.Equal(
            "code.exe",
            result.ProcessName);

        Assert.Null(
            result.WindowTitle);
    }

    [Fact]
    public void FromSnapshot_BoundsTitle_WhenEnabled()
    {
        ForegroundAppSnapshot snapshot =
            new()
            {
                ProcessName = "notepad.exe",
                WindowTitle = "1234567890",
                ObservedAt =
                    DateTimeOffset.UtcNow,
                ProcessId = 456,
            };

        AppTrackingOptions options =
            new()
            {
                Enabled = true,
                CaptureWindowTitles = true,
                MaximumWindowTitleLength = 5,
                MonitoringDisclosureRequired = true,
            };

        AppTrackingObservation result =
            AppTrackingObservation.FromSnapshot(
                snapshot,
                options);

        Assert.Equal(
            "12345",
            result.WindowTitle);
    }

    [Fact]
    public void RepresentsSameApplication_IsCaseInsensitive()
    {
        AppTrackingObservation first =
            new()
            {
                ProcessName =
                    "Chrome.EXE",
                ExecutablePath =
                    @"C:\Chrome\chrome.exe",
                ObservedAt =
                    DateTimeOffset.UtcNow,
            };

        AppTrackingObservation second =
            new()
            {
                ProcessName =
                    "chrome.exe",
                ExecutablePath =
                    @"c:\chrome\CHROME.EXE",
                ObservedAt =
                    DateTimeOffset.UtcNow,
            };

        Assert.True(
            first.RepresentsSameApplication(
                second));
    }
}