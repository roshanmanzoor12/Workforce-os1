namespace WorkforceOS.WebsiteNativeHost;

public static class NativeHostAgentLocator
{
    private const string AgentExecutableName =
        "WorkforceOS.Agent.exe";

    public static string? FindAgentExecutable()
    {
        string baseDirectory =
            AppContext.BaseDirectory;

        string besideLauncher =
            Path.Combine(
                baseDirectory,
                AgentExecutableName
            );

        if (
            File.Exists(
                besideLauncher
            )
        )
        {
            return Path.GetFullPath(
                besideLauncher
            );
        }

        string developmentPath =
            Path.Combine(
                @"C:\workforce-os",
                "artifacts",
                "agent",
                "win-x64",
                AgentExecutableName
            );

        if (
            File.Exists(
                developmentPath
            )
        )
        {
            return Path.GetFullPath(
                developmentPath
            );
        }

        return null;
    }
}