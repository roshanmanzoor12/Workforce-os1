namespace WorkforceOS.Agent.AppTracking;

public static class AppTrackingHelperBootstrap
{
    public static bool IsRequested(
        string[] args)
    {
        ArgumentNullException.ThrowIfNull(
            args);

        return AppTrackingCommandLine.IsSessionHelper(
            args);
    }

    public static async Task<int> RunAsync(
        IServiceProvider services,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(
            services);

        return await AppTrackingCommandLine
            .RunSessionHelperAsync(
                services,
                cancellationToken);
    }
}