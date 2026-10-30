namespace WorkforceOS.Agent.AppTracking;

public sealed class AppTrackingOptions
{
    public const string SectionName =
        "AppTracking";

    public bool Enabled { get; set; } =
        true;

    public int ObservationIntervalSeconds { get; set; } =
        15;

    public int ReportIntervalSeconds { get; set; } =
        30;

    public bool CaptureWindowTitles { get; set; } =
        false;

    public int MaximumWindowTitleLength { get; set; } =
        512;

    public bool MonitoringDisclosureRequired { get; set; } =
        true;

    public void Validate()
    {
        if (ObservationIntervalSeconds < 5)
        {
            throw new InvalidOperationException(
                "AppTracking ObservationIntervalSeconds must be at least 5.");
        }

        if (ReportIntervalSeconds < 5)
        {
            throw new InvalidOperationException(
                "AppTracking ReportIntervalSeconds must be at least 5.");
        }

        if (
            MaximumWindowTitleLength < 1
            || MaximumWindowTitleLength > 4096)
        {
            throw new InvalidOperationException(
                "AppTracking MaximumWindowTitleLength must be between 1 and 4096.");
        }

        if (!MonitoringDisclosureRequired)
        {
            throw new InvalidOperationException(
                "WorkforceOS app tracking requires monitoring disclosure.");
        }
    }
}