namespace WorkforceOS.Agent.WebsiteTracking;

public sealed class WebsiteTrackingOptions
{
    public const string SectionName =
        "WebsiteTracking";

    public bool Enabled
    {
        get;
        set;
    } = true;

    public int ObservationIntervalSeconds
    {
        get;
        set;
    } = 15;

    public int ReportIntervalSeconds
    {
        get;
        set;
    } = 30;

    public bool CaptureFullUrls
    {
        get;
        set;
    } = false;

    public bool CapturePageTitles
    {
        get;
        set;
    } = false;

    public int MaximumDomainLength
    {
        get;
        set;
    } = 255;

    public int MaximumUrlLength
    {
        get;
        set;
    } = 8192;

    public int MaximumPageTitleLength
    {
        get;
        set;
    } = 1024;

    public bool MonitoringDisclosureRequired
    {
        get;
        set;
    } = true;
}