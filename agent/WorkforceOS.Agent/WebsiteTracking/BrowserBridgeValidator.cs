namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class BrowserBridgeValidator
{
    public bool TryConvert(
        BrowserBridgeMessage message,
        out WebsiteTrackingObservation observation,
        out string? error
    )
    {
        ArgumentNullException.ThrowIfNull(
            message
        );

        observation =
            null!;

        error =
            null;

        if (
            message.ProtocolVersion
            != WebsiteTrackingPipeNames
                .ProtocolVersion
        )
        {
            error =
                "Unsupported browser bridge protocol version.";

            return false;
        }

        if (
            string.IsNullOrWhiteSpace(
                message.BrowserProcessName
            )
        )
        {
            error =
                "Browser process name is required.";

            return false;
        }

        if (
            !BrowserSupportCatalog
                .TryGetBrowserName(
                    message.BrowserProcessName,
                    out string browserName
                )
        )
        {
            error =
                "Unsupported browser.";

            return false;
        }

        if (
            string.IsNullOrWhiteSpace(
                message.Domain
            )
        )
        {
            error =
                "Domain is required.";

            return false;
        }

        string domain =
            message
                .Domain
                .Trim()
                .ToLowerInvariant();

        if (
            domain.Contains(
                "/",
                StringComparison.Ordinal
            )
            || domain.Contains(
                "?",
                StringComparison.Ordinal
            )
            || domain.Contains(
                "#",
                StringComparison.Ordinal
            )
        )
        {
            error =
                "Browser bridge must send hostname only.";

            return false;
        }

        observation =
            new WebsiteTrackingObservation
            {
                BrowserName =
                    browserName,

                BrowserProcessName =
                    BrowserSupportCatalog
                        .NormalizeProcessName(
                            message
                                .BrowserProcessName
                        ),

                Domain =
                    domain,

                PageUrl =
                    message.PageUrl,

                PageTitle =
                    message.PageTitle,

                ObservedAt =
                    message.ObservedAt,
            };

        return true;
    }
}