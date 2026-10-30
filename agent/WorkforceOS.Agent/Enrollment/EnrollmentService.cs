using Microsoft.Extensions.Logging;
using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Enrollment;

public sealed class EnrollmentService
{
    private readonly MachineIdentityProvider
        _machineIdentityProvider;

    private readonly WorkforceApiClient
        _apiClient;

    private readonly DeviceCredentialStore
        _credentialStore;

    private readonly ILogger<EnrollmentService>
        _logger;

    public EnrollmentService(
        MachineIdentityProvider machineIdentityProvider,
        WorkforceApiClient apiClient,
        DeviceCredentialStore credentialStore,
        ILogger<EnrollmentService> logger
    )
    {
        _machineIdentityProvider =
            machineIdentityProvider;

        _apiClient =
            apiClient;

        _credentialStore =
            credentialStore;

        _logger =
            logger;
    }

    // =====================================================
    // CURRENT ENROLLMENT STATE
    // =====================================================

    public async Task<bool> IsEnrolledAsync(
        CancellationToken cancellationToken = default
    )
    {
        DeviceCredentials? credentials =
            await _credentialStore.LoadAsync(
                cancellationToken
            );

        return
            credentials is not null
            && credentials.IsValid();
    }

    public Task<DeviceCredentials?> GetCredentialsAsync(
        CancellationToken cancellationToken = default
    )
    {
        return _credentialStore.LoadAsync(
            cancellationToken
        );
    }

    // =====================================================
    // ENROLLMENT
    // =====================================================

    public async Task<DeviceCredentials> EnrollAsync(
        string activationCode,
        CancellationToken cancellationToken = default
    )
    {
        string normalizedActivationCode =
            NormalizeActivationCode(
                activationCode
            );

        DeviceCredentials? existingCredentials =
            await _credentialStore.LoadAsync(
                cancellationToken
            );

        if (
            existingCredentials is not null
            && existingCredentials.IsValid()
        )
        {
            throw new InvalidOperationException(
                "This WorkforceOS Agent installation is already enrolled."
            );
        }

        MachineIdentity identity =
            await _machineIdentityProvider.GetAsync(
                cancellationToken
            );

        DeviceRegistrationRequest request =
            new()
            {
                ActivationCode =
                    normalizedActivationCode,

                Hostname =
                    identity.Hostname,

                OsName =
                    identity.OperatingSystem,

                OsVersion =
                    identity.OperatingSystemVersion,

                Architecture =
                    identity.Architecture,

                AgentVersion =
                    identity.AgentVersion,

                AgentIdentifier =
                    identity.AgentIdentifier
            };

        _logger.LogInformation(
            "Registering WorkforceOS Agent for machine {Hostname}.",
            identity.Hostname
        );

        DeviceRegistrationResponse response =
            await _apiClient.RegisterDeviceAsync(
                request,
                cancellationToken
            );

        DeviceCredentials credentials =
            new()
            {
                DeviceUuid =
                    response.Credential.DeviceUuid,

                DeviceSecret =
                    response.Credential.DeviceSecret,

                StoredAt =
                    DateTimeOffset.UtcNow,

                FormatVersion =
                    1
            };

        if (
            !credentials.IsValid()
        )
        {
            throw new InvalidOperationException(
                "Backend returned invalid WorkforceOS device credentials."
            );
        }

        await _credentialStore.SaveAsync(
            credentials,
            cancellationToken
        );

        _logger.LogInformation(
            "WorkforceOS Agent enrollment completed for device {DeviceUuid}.",
            credentials.DeviceUuid
        );

        return credentials;
    }

    // =====================================================
    // LOCAL RESET
    // =====================================================

    public async Task ClearLocalEnrollmentAsync(
        CancellationToken cancellationToken = default
    )
    {
        await _credentialStore.DeleteAsync(
            cancellationToken
        );

        _logger.LogInformation(
            "Local WorkforceOS Agent enrollment credentials were removed."
        );
    }

    // =====================================================
    // HELPERS
    // =====================================================

    private static string NormalizeActivationCode(
        string activationCode
    )
    {
        if (
            string.IsNullOrWhiteSpace(
                activationCode
            )
        )
        {
            throw new ArgumentException(
                "Activation code is required.",
                nameof(activationCode)
            );
        }

        string normalized =
            activationCode.Trim();

        if (
            normalized.Length < 6
        )
        {
            throw new ArgumentException(
                "Activation code is invalid.",
                nameof(activationCode)
            );
        }

        if (
            normalized.Length > 256
        )
        {
            throw new ArgumentException(
                "Activation code is invalid.",
                nameof(activationCode)
            );
        }

        return normalized;
    }
}