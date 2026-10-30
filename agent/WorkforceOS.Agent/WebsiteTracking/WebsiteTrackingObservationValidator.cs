using Microsoft.Extensions.Options;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingObservationValidator
{
    private readonly
        WebsiteTrackingOptions
        _options;

    public WebsiteTrackingObservationValidator(
        IOptions<WebsiteTrackingOptions> options
    )
    {
        ArgumentNullException.ThrowIfNull(
            options
        );

        _options =
            options.Value;
    }

    public bool TryValidateAndNormalize(
        WebsiteTrackingObservation observation,
        out WebsiteTrackingObservation
            normalizedObservation,
        out string? validationError
    )
    {
        normalizedObservation =
            observation;

        validationError =
            null;

        if (
            !_options.Enabled
        )
        {
            validationError =
                "Website Tracking is disabled.";

            return false;
        }

        if (
            _options
                .MonitoringDisclosureRequired
            == false
        )
        {
            validationError =
                "Monitoring disclosure requirement must remain enabled.";

            return false;
        }

        string browserProcessName =
            BrowserSupportCatalog
                .NormalizeProcessName(
                    observation
                        .BrowserProcessName
                );

        if (
            !BrowserSupportCatalog
                .TryGetBrowserName(
                    browserProcessName,
                    out string browserName
                )
        )
        {
            validationError =
                "Unsupported browser process.";

            return false;
        }

        string domain =
            observation
                .Domain
                .Trim()
                .ToLowerInvariant();

        if (
            string.IsNullOrWhiteSpace(
                domain
            )
        )
        {
            validationError =
                "Website domain is required.";

            return false;
        }

        if (
            domain.Length
            > _options.MaximumDomainLength
        )
        {
            validationError =
                "Website domain exceeds maximum length.";

            return false;
        }

        if (
            domain.Contains(
                '/',
                StringComparison.Ordinal
            )
            || domain.Contains(
                '?',
                StringComparison.Ordinal
            )
            || domain.Contains(
                '#',
                StringComparison.Ordinal
            )
        )
        {
            validationError =
                "Website observation must contain a hostname/domain, not a URL.";

            return false;
        }

        if (
            observation.ObservedAt
            > DateTimeOffset.UtcNow.AddMinutes(
                5
            )
        )
        {
            validationError =
                "Website observation timestamp is too far in the future.";

            return false;
        }

        string? pageUrl =
            null;

        if (
            _options.CaptureFullUrls
            && !string.IsNullOrWhiteSpace(
                observation.PageUrl
            )
        )
        {
            pageUrl =
                observation
                    .PageUrl
                    .Trim();

            if (
                pageUrl.Length
                > _options.MaximumUrlLength
            )
            {
                pageUrl =
                    pageUrl[
                        .._options
                            .MaximumUrlLength
                    ];
            }
        }

        string? pageTitle =
            null;

        if (
            _options.CapturePageTitles
            && !string.IsNullOrWhiteSpace(
                observation.PageTitle
            )
        )
        {
            pageTitle =
                observation
                    .PageTitle
                    .Trim();

            if (
                pageTitle.Length
                > _options
                    .MaximumPageTitleLength
            )
            {
                pageTitle =
                    pageTitle[
                        .._options
                            .MaximumPageTitleLength
                    ];
            }
        }

        normalizedObservation =
            observation
                with
                {
                    BrowserName =
                        browserName,

                    BrowserProcessName =
                        browserProcessName,

                    Domain =
                        domain,

                    PageUrl =
                        pageUrl,

                    PageTitle =
                        pageTitle,
                };

        return true;
    }
}