namespace WorkforceOS.Agent.AppTracking;

public static class AppTrackingCommandLine
{
    public const string SessionHelperArgument =
        "--app-tracking-session-helper";

    public static bool IsSessionHelper(
        IReadOnlyList<string> arguments)
    {
        ArgumentNullException.ThrowIfNull(
            arguments);

        return arguments.Any(
            argument =>
                string.Equals(
                    argument,
                    SessionHelperArgument,
                    StringComparison.OrdinalIgnoreCase));
    }

    public static async Task<int> RunSessionHelperAsync(
        IServiceProvider serviceProvider,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(
            serviceProvider);

        AppTrackingSessionHelperCommand? command =
            serviceProvider.GetService(
                typeof(
                    AppTrackingSessionHelperCommand))
            as AppTrackingSessionHelperCommand;

        if (command is null)
        {
            throw new InvalidOperationException(
                "AppTrackingSessionHelperCommand is not registered.");
        }

        return await command.RunAsync(
            cancellationToken);
    }
}