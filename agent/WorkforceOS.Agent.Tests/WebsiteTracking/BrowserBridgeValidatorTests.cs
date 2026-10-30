using WorkforceOS.Agent.WebsiteTracking;
using Xunit;

namespace WorkforceOS.Agent.Tests.WebsiteTracking;

public sealed class BrowserBridgeValidatorTests
{
    [Fact]
    public void ValidDomainMessageAccepted()
    {
        BrowserBridgeValidator
            validator =
                new();

        BrowserBridgeMessage
            message =
                new()
                {
                    ProtocolVersion =
                        1,

                    BrowserProcessName =
                        "chrome.exe",

                    Domain =
                        "github.com",

                    ObservedAt =
                        DateTimeOffset.UtcNow,
                };

        bool result =
            validator.TryConvert(
                message,
                out WebsiteTrackingObservation
                    observation,
                out string? error
            );

        Assert.True(
            result
        );

        Assert.Null(
            error
        );

        Assert.Equal(
            "Google Chrome",
            observation.BrowserName
        );

        Assert.Equal(
            "github.com",
            observation.Domain
        );
    }

    [Fact]
    public void FullUrlAsDomainRejected()
    {
        BrowserBridgeValidator
            validator =
                new();

        BrowserBridgeMessage
            message =
                new()
                {
                    ProtocolVersion =
                        1,

                    BrowserProcessName =
                        "chrome.exe",

                    Domain =
                        "https://github.com/test",

                    ObservedAt =
                        DateTimeOffset.UtcNow,
                };

        bool result =
            validator.TryConvert(
                message,
                out _,
                out string? error
            );

        Assert.False(
            result
        );

        Assert.NotNull(
            error
        );
    }

    [Fact]
    public void UnsupportedBrowserRejected()
    {
        BrowserBridgeValidator
            validator =
                new();

        BrowserBridgeMessage
            message =
                new()
                {
                    ProtocolVersion =
                        1,

                    BrowserProcessName =
                        "notepad.exe",

                    Domain =
                        "example.com",

                    ObservedAt =
                        DateTimeOffset.UtcNow,
                };

        Assert.False(
            validator.TryConvert(
                message,
                out _,
                out _
            )
        );
    }
}