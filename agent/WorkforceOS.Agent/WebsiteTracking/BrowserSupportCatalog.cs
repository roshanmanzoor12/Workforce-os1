namespace WorkforceOS.Agent.WebsiteTracking;

public static class BrowserSupportCatalog
{
    private static readonly
        IReadOnlyDictionary<string, string>
        BrowserNames =
            new Dictionary<
                string,
                string
            >(
                StringComparer.OrdinalIgnoreCase
            )
            {
                [
                    "chrome.exe"
                ] =
                    "Google Chrome",

                [
                    "msedge.exe"
                ] =
                    "Microsoft Edge",

                [
                    "firefox.exe"
                ] =
                    "Mozilla Firefox",

                [
                    "brave.exe"
                ] =
                    "Brave",

                [
                    "opera.exe"
                ] =
                    "Opera",

                [
                    "opera_gx.exe"
                ] =
                    "Opera GX",

                [
                    "vivaldi.exe"
                ] =
                    "Vivaldi",
            };

    public static bool IsSupported(
        string? processName
    )
    {
        if (
            string.IsNullOrWhiteSpace(
                processName
            )
        )
        {
            return false;
        }

        return BrowserNames.ContainsKey(
            NormalizeProcessName(
                processName
            )
        );
    }

    public static bool TryGetBrowserName(
        string? processName,
        out string browserName
    )
    {
        browserName =
            string.Empty;

        if (
            string.IsNullOrWhiteSpace(
                processName
            )
        )
        {
            return false;
        }

        return BrowserNames.TryGetValue(
            NormalizeProcessName(
                processName
            ),
            out browserName!
        );
    }

    public static string? GetBrowserName(
        string? processName
    )
    {
        if (
            TryGetBrowserName(
                processName,
                out string browserName
            )
        )
        {
            return browserName;
        }

        return null;
    }

    public static string NormalizeProcessName(
        string processName
    )
    {
        string normalized =
            processName
                .Trim()
                .ToLowerInvariant();

        if (
            !normalized.EndsWith(
                ".exe",
                StringComparison.OrdinalIgnoreCase
            )
        )
        {
            normalized +=
                ".exe";
        }

        return normalized;
    }

    public static IReadOnlyCollection<
        string
    > GetSupportedProcesses()
    {
        return BrowserNames
            .Keys
            .OrderBy(
                value => value,
                StringComparer.OrdinalIgnoreCase
            )
            .ToArray();
    }
}