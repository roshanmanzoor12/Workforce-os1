using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class BrowserSupportCatalogTests
{
    [Theory]
    [InlineData(
        "chrome.exe",
        "Google Chrome"
    )]
    [InlineData(
        "chrome",
        "Google Chrome"
    )]
    [InlineData(
        "msedge.exe",
        "Microsoft Edge"
    )]
    [InlineData(
        "firefox.exe",
        "Mozilla Firefox"
    )]
    [InlineData(
        "brave.exe",
        "Brave"
    )]
    public void SupportedBrowserResolves(
        string processName,
        string expectedBrowserName
    )
    {
        bool result =
            BrowserSupportCatalog
                .TryGetBrowserName(
                    processName,
                    out string browserName
                );

        Assert.True(
            result
        );

        Assert.Equal(
            expectedBrowserName,
            browserName
        );
    }

    [Fact]
    public void UnsupportedProcessRejected()
    {
        Assert.False(
            BrowserSupportCatalog.IsSupported(
                "notepad.exe"
            )
        );
    }

    [Theory]
    [InlineData(
        "CHROME",
        "chrome.exe"
    )]
    [InlineData(
        " chrome.exe ",
        "chrome.exe"
    )]
    public void ProcessNormalizationWorks(
        string input,
        string expected
    )
    {
        Assert.Equal(
            expected,
            BrowserSupportCatalog
                .NormalizeProcessName(
                    input
                )
        );
    }
}