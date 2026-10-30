using System.Runtime.InteropServices;
using Microsoft.Extensions.Options;
using WorkforceOS.Agent.Configuration;

namespace WorkforceOS.Agent.Enrollment;

public sealed class MachineIdentityProvider
{
    private const string AgentDataDirectoryName =
        "WorkforceOS";

    private const string AgentSubdirectoryName =
        "Agent";

    private const string AgentIdentifierFileName =
        "agent-id";

    private readonly AgentOptions _options;

    public MachineIdentityProvider(
        IOptions<AgentOptions> options
    )
    {
        _options = options.Value;
    }

    public async Task<MachineIdentity> GetAsync(
        CancellationToken cancellationToken = default
    )
    {
        string agentIdentifier =
            await GetOrCreateAgentIdentifierAsync(
                cancellationToken
            );

        return new MachineIdentity
        {
            Hostname =
                Environment.MachineName,

            OperatingSystem =
                RuntimeInformation.OSDescription.Trim(),

            OperatingSystemVersion =
                Environment.OSVersion.VersionString,

            Architecture =
                RuntimeInformation.OSArchitecture.ToString(),

            AgentVersion =
                _options.AgentVersion,

            AgentIdentifier =
                agentIdentifier
        };
    }

    private static async Task<string>
        GetOrCreateAgentIdentifierAsync(
            CancellationToken cancellationToken
        )
    {
        string directoryPath =
            GetAgentDataDirectory();

        Directory.CreateDirectory(
            directoryPath
        );

        string filePath =
            Path.Combine(
                directoryPath,
                AgentIdentifierFileName
            );

        string? existingIdentifier =
            await ReadValidIdentifierAsync(
                filePath,
                cancellationToken
            );

        if (
            !string.IsNullOrWhiteSpace(
                existingIdentifier
            )
        )
        {
            return existingIdentifier;
        }

        string newIdentifier =
            Guid.NewGuid().ToString(
                "N"
            );

        try
        {
            await using FileStream stream =
                new(
                    filePath,
                    FileMode.CreateNew,
                    FileAccess.Write,
                    FileShare.Read
                );

            await using StreamWriter writer =
                new(
                    stream
                );

            await writer.WriteAsync(
                newIdentifier.AsMemory(),
                cancellationToken
            );

            await writer.FlushAsync(
                cancellationToken
            );

            return newIdentifier;
        }
        catch (IOException)
        {
            existingIdentifier =
                await ReadValidIdentifierAsync(
                    filePath,
                    cancellationToken
                );

            if (
                !string.IsNullOrWhiteSpace(
                    existingIdentifier
                )
            )
            {
                return existingIdentifier;
            }

            await File.WriteAllTextAsync(
                filePath,
                newIdentifier,
                cancellationToken
            );

            return newIdentifier;
        }
    }

    private static async Task<string?>
        ReadValidIdentifierAsync(
            string filePath,
            CancellationToken cancellationToken
        )
    {
        if (
            !File.Exists(
                filePath
            )
        )
        {
            return null;
        }

        string value =
            (
                await File.ReadAllTextAsync(
                    filePath,
                    cancellationToken
                )
            ).Trim();

        if (
            !Guid.TryParseExact(
                value,
                "N",
                out _
            )
        )
        {
            return null;
        }

        return value;
    }

    private static string GetAgentDataDirectory()
    {
        string commonApplicationData =
            Environment.GetFolderPath(
                Environment.SpecialFolder
                    .CommonApplicationData
            );

        if (
            string.IsNullOrWhiteSpace(
                commonApplicationData
            )
        )
        {
            throw new InvalidOperationException(
                "Windows common application data directory could not be resolved."
            );
        }

        return Path.Combine(
            commonApplicationData,
            AgentDataDirectoryName,
            AgentSubdirectoryName
        );
    }
}