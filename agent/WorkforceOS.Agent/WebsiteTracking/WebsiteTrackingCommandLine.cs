namespace WorkforceOS.Agent.WebsiteTracking;

public static class WebsiteTrackingCommandLine
{
    public const string NativeHostArgument =
        "--website-tracking-native-host";

    public static bool IsNativeHostRequested(
        IReadOnlyCollection<string> args
    )
    {
        ArgumentNullException.ThrowIfNull(
            args
        );

        return args.Any(
            argument =>
                string.Equals(
                    argument,
                    NativeHostArgument,
                    StringComparison.OrdinalIgnoreCase
                )
        );
    }

    public static string[] RemoveNativeHostArgument(
        IReadOnlyCollection<string> args
    )
    {
        ArgumentNullException.ThrowIfNull(
            args
        );

        return args
            .Where(
                argument =>
                    !string.Equals(
                        argument,
                        NativeHostArgument,
                        StringComparison.OrdinalIgnoreCase
                    )
            )
            .ToArray();
    }
}