namespace WorkforceOS.Agent.Enrollment;

public sealed record MachineIdentity
{
    public required string Hostname { get; init; }

    public required string OperatingSystem { get; init; }

    public required string OperatingSystemVersion { get; init; }

    public required string Architecture { get; init; }

    public required string AgentVersion { get; init; }

    public required string AgentIdentifier { get; init; }
}