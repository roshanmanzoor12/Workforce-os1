namespace WorkforceOS.WebsiteNativeHost;

public static class Program
{
    public static async Task<int> Main(
        string[] args
    )
    {
        string? agentPath =
            NativeHostAgentLocator
                .FindAgentExecutable();

        if (
            string.IsNullOrWhiteSpace(
                agentPath
            )
        )
        {
            return 2;
        }

        try
        {
            return await NativeHostProxy.RunAsync(
                agentPath,
                CancellationToken.None
            );
        }
        catch
        {
            /*
             * Never write normal diagnostic output to stdout.
             * Chromium Native Messaging reserves stdout for its
             * framed binary protocol.
             */
            return 1;
        }
    }
}