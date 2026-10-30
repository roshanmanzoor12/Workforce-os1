using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class WebsiteTrackingCommandLineTests
{
    [Fact]
    public void NativeHostArgumentDetected()
    {
        string[] args =
        {
            "--website-tracking-native-host",
        };

        Assert.True(
            WebsiteTrackingCommandLine
                .IsNativeHostRequested(
                    args
                )
        );
    }

    [Fact]
    public void NativeHostArgumentDetectionIsCaseInsensitive()
    {
        string[] args =
        {
            "--WEBSITE-TRACKING-NATIVE-HOST",
        };

        Assert.True(
            WebsiteTrackingCommandLine
                .IsNativeHostRequested(
                    args
                )
        );
    }

    [Fact]
    public void NativeHostArgumentRemoved()
    {
        string[] args =
        {
            "--website-tracking-native-host",
            "--environment",
            "Development",
        };

        string[] result =
            WebsiteTrackingCommandLine
                .RemoveNativeHostArgument(
                    args
                );

        Assert.DoesNotContain(
            "--website-tracking-native-host",
            result
        );

        Assert.Contains(
            "--environment",
            result
        );
    }
}