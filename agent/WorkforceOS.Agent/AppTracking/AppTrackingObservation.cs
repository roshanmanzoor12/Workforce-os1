namespace WorkforceOS.Agent.AppTracking;

public sealed record AppTrackingObservation
{
    public required string ProcessName { get; init; }

    public string? ExecutablePath { get; init; }

    public string? WindowTitle { get; init; }

    public required DateTimeOffset ObservedAt { get; init; }

    public static AppTrackingObservation FromSnapshot(
        ForegroundAppSnapshot snapshot,
        AppTrackingOptions options)
    {
        ArgumentNullException.ThrowIfNull(
            snapshot);

        ArgumentNullException.ThrowIfNull(
            options);

        options.Validate();

        string? windowTitle =
            null;

        if (
            options.CaptureWindowTitles
            && !string.IsNullOrWhiteSpace(
                snapshot.WindowTitle))
        {
            string normalized =
                snapshot.WindowTitle.Trim();

            windowTitle =
                normalized.Length
                    <= options.MaximumWindowTitleLength
                    ? normalized
                    : normalized[
                        ..options.MaximumWindowTitleLength];
        }

        return new AppTrackingObservation
        {
            ProcessName =
                snapshot.ProcessName.Trim(),

            ExecutablePath =
                string.IsNullOrWhiteSpace(
                    snapshot.ExecutablePath)
                    ? null
                    : snapshot.ExecutablePath.Trim(),

            WindowTitle =
                windowTitle,

            ObservedAt =
                snapshot.ObservedAt,
        };
    }

    public bool RepresentsSameApplication(
        AppTrackingObservation other)
    {
        ArgumentNullException.ThrowIfNull(
            other);

        return string.Equals(
                ProcessName,
                other.ProcessName,
                StringComparison.OrdinalIgnoreCase)
            &&
            string.Equals(
                ExecutablePath ?? string.Empty,
                other.ExecutablePath ?? string.Empty,
                StringComparison.OrdinalIgnoreCase);
    }
}