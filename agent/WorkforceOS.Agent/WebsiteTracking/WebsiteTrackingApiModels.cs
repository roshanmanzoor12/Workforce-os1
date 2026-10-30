using System.Text.Json.Serialization;

namespace WorkforceOS.Agent.WebsiteTracking;

public sealed record WebsiteTrackingApiObservationRequest
{
    [JsonPropertyName(
        "browser_name"
    )]
    public required string BrowserName
    {
        get;
        init;
    }

    [JsonPropertyName(
        "browser_process_name"
    )]
    public required string BrowserProcessName
    {
        get;
        init;
    }

    [JsonPropertyName(
        "domain"
    )]
    public required string Domain
    {
        get;
        init;
    }

    [JsonPropertyName(
        "page_url"
    )]
    public string? PageUrl
    {
        get;
        init;
    }

    [JsonPropertyName(
        "page_title"
    )]
    public string? PageTitle
    {
        get;
        init;
    }

    [JsonPropertyName(
        "observed_at"
    )]
    public required DateTimeOffset ObservedAt
    {
        get;
        init;
    }

    public static
        WebsiteTrackingApiObservationRequest
        FromObservation(
            WebsiteTrackingObservation
                observation
        )
    {
        ArgumentNullException.ThrowIfNull(
            observation
        );

        return new WebsiteTrackingApiObservationRequest
        {
            BrowserName =
                observation.BrowserName,

            BrowserProcessName =
                observation.BrowserProcessName,

            Domain =
                observation.Domain,

            PageUrl =
                observation.PageUrl,

            PageTitle =
                observation.PageTitle,

            ObservedAt =
                observation.ObservedAt,
        };
    }
}


public sealed record
    WebsiteTrackingApiObservationResponse
{
    [JsonPropertyName(
        "previous_interval_closed"
    )]
    public bool PreviousIntervalClosed
    {
        get;
        init;
    }

    [JsonPropertyName(
        "ignored_as_old"
    )]
    public bool IgnoredAsOld
    {
        get;
        init;
    }
}