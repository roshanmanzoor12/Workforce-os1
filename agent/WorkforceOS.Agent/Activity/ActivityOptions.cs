namespace WorkforceOS.Agent.Activity;

public sealed class ActivityOptions
{
    public const string SectionName =
        "Activity";

    public int IdleThresholdSeconds
    {
        get;
        set;
    } = 300;

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

    public bool Enabled
    {
        get;
        set;
    } = true;

    public bool MonitoringDisclosureRequired
    {
        get;
        set;
    } = true;
}