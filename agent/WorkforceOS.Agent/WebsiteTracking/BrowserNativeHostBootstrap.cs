using Microsoft.Extensions.DependencyInjection;

namespace WorkforceOS.Agent.WebsiteTracking;

public static class BrowserNativeHostBootstrap
{
    public static bool IsRequested(
        IReadOnlyCollection<string> args
    )
    {
        return WebsiteTrackingCommandLine
            .IsNativeHostRequested(
                args
            );
    }

    public static async Task<int> RunAsync(
        IServiceProvider services,
        CancellationToken cancellationToken
    )
    {
        ArgumentNullException.ThrowIfNull(
            services
        );

        BrowserNativeHostCommand command =
            services.GetRequiredService<
                BrowserNativeHostCommand
            >();

        return await command.RunAsync(
            cancellationToken
        );
    }
}