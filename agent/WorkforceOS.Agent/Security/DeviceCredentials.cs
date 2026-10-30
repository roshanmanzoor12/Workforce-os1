namespace WorkforceOS.Agent.Security;

public sealed record DeviceCredentials
{
    public const int CurrentFormatVersion =
        2;

    public required Guid DeviceUuid
    {
        get;
        init;
    }

    public required string DeviceSecret
    {
        get;
        init;
    }

    public required DateTimeOffset StoredAt
    {
        get;
        init;
    }

    public required int FormatVersion
    {
        get;
        init;
    } =
        CurrentFormatVersion;

    public bool IsValid()
    {
        return
            DeviceUuid != Guid.Empty
            && !string.IsNullOrWhiteSpace(
                DeviceSecret
            )
            && DeviceSecret.Length >= 20
            && FormatVersion >= 1
            && FormatVersion
                <= CurrentFormatVersion;
    }

    public bool RequiresMigration()
    {
        return
            FormatVersion
            < CurrentFormatVersion;
    }
}