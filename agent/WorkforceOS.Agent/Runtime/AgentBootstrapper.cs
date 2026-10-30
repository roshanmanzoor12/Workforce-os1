using WorkforceOS.Agent.Api;
using WorkforceOS.Agent.Enrollment;
using WorkforceOS.Agent.Security;

namespace WorkforceOS.Agent.Runtime;

public sealed class AgentBootstrapper
{
    private readonly EnrollmentService
        _enrollmentService;

    private readonly WorkforceApiClient
        _apiClient;

    private readonly DevicePresenceClient
        _presenceClient;

    public AgentBootstrapper(
        EnrollmentService enrollmentService,
        WorkforceApiClient apiClient,
        DevicePresenceClient presenceClient
    )
    {
        _enrollmentService =
            enrollmentService;

        _apiClient =
            apiClient;

        _presenceClient =
            presenceClient;
    }

    public async Task<int> ExecuteAsync(
        AgentCommandLineOptions options,
        CancellationToken cancellationToken = default
    )
    {
        ArgumentNullException.ThrowIfNull(
            options
        );

        return options.Mode switch
        {
            AgentCommandMode.Enroll =>
                await ExecuteEnrollmentAsync(
                    cancellationToken
                ),

            AgentCommandMode.Status =>
                await ExecuteStatusAsync(
                    cancellationToken
                ),

            AgentCommandMode.Presence =>
                await ExecutePresenceAsync(
                    cancellationToken
                ),

            AgentCommandMode.ResetEnrollment =>
                await ExecuteResetEnrollmentAsync(
                    cancellationToken
                ),

            _ =>
                throw new InvalidOperationException(
                    "Bootstrapper cannot execute normal agent runtime mode."
                )
        };
    }

    // =====================================================
    // ENROLLMENT
    // =====================================================

    private async Task<int> ExecuteEnrollmentAsync(
        CancellationToken cancellationToken
    )
    {
        try
        {
            DeviceCredentials? existingCredentials =
                await _enrollmentService
                    .GetCredentialsAsync(
                        cancellationToken
                    );

            if (
                existingCredentials is not null
                && existingCredentials.IsValid()
            )
            {
                Console.WriteLine(
                    "WorkforceOS Agent is already enrolled."
                );

                Console.WriteLine(
                    $"Device UUID: {existingCredentials.DeviceUuid:D}"
                );

                Console.WriteLine(
                    "Run with --status to verify backend authentication."
                );

                return 2;
            }

            string activationCode =
                ActivationCodePrompt.Read();

            Console.WriteLine(
                "Registering WorkforceOS Agent..."
            );

            DeviceCredentials credentials =
                await _enrollmentService
                    .EnrollAsync(
                        activationCode,
                        cancellationToken
                    );

            Console.WriteLine(
                "Device registration completed."
            );

            Console.WriteLine(
                $"Device UUID: {credentials.DeviceUuid:D}"
            );

            Console.WriteLine(
                "Verifying device authentication..."
            );

            DeviceAgentAuthenticationResult authentication =
                await _apiClient
                    .AuthenticateDeviceAsync(
                        credentials,
                        cancellationToken
                    );

            Console.WriteLine(
                "Device authentication succeeded."
            );

            Console.WriteLine(
                $"Authenticated Device UUID: {authentication.DeviceUuid:D}"
            );

            if (
                !string.IsNullOrWhiteSpace(
                    authentication.Status
                )
            )
            {
                Console.WriteLine(
                    $"Device Status: {authentication.Status}"
                );
            }

            return 0;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            Console.Error.WriteLine(
                "Operation cancelled."
            );

            return 1;
        }
        catch (
            Exception exception
        )
        when (
            exception
                is WorkforceApiException
                or ArgumentException
                or InvalidOperationException
                or InvalidDataException
                or HttpRequestException
        )
        {
            Console.Error.WriteLine(
                exception.Message
            );

            return 1;
        }
    }

    // =====================================================
    // STATUS
    // =====================================================

    private async Task<int> ExecuteStatusAsync(
        CancellationToken cancellationToken
    )
    {
        try
        {
            DeviceCredentials? credentials =
                await _enrollmentService
                    .GetCredentialsAsync(
                        cancellationToken
                    );

            if (
                credentials is null
                || !credentials.IsValid()
            )
            {
                Console.WriteLine(
                    "WorkforceOS Agent is not enrolled."
                );

                return 2;
            }

            Console.WriteLine(
                "Local WorkforceOS enrollment found."
            );

            Console.WriteLine(
                $"Device UUID: {credentials.DeviceUuid:D}"
            );

            Console.WriteLine(
                $"Credential Format: {credentials.FormatVersion}"
            );

            Console.WriteLine(
                "Checking backend authentication..."
            );

            DeviceAgentAuthenticationResult authentication =
                await _apiClient
                    .AuthenticateDeviceAsync(
                        credentials,
                        cancellationToken
                    );

            Console.WriteLine(
                "Backend authentication succeeded."
            );

            Console.WriteLine(
                $"Authenticated Device UUID: {authentication.DeviceUuid:D}"
            );

            if (
                !string.IsNullOrWhiteSpace(
                    authentication.Status
                )
            )
            {
                Console.WriteLine(
                    $"Device Status: {authentication.Status}"
                );
            }

            return 0;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            Console.Error.WriteLine(
                "Operation cancelled."
            );

            return 1;
        }
        catch (
            Exception exception
        )
        when (
            exception
                is WorkforceApiException
                or HttpRequestException
                or InvalidDataException
        )
        {
            Console.Error.WriteLine(
                exception.Message
            );

            return 1;
        }
    }

    // =====================================================
    // PRESENCE
    // =====================================================

    private async Task<int> ExecutePresenceAsync(
        CancellationToken cancellationToken
    )
    {
        try
        {
            DeviceCredentials? credentials =
                await _enrollmentService
                    .GetCredentialsAsync(
                        cancellationToken
                    );

            if (
                credentials is null
                || !credentials.IsValid()
            )
            {
                Console.WriteLine(
                    "WorkforceOS Agent is not enrolled."
                );

                return 2;
            }

            Console.WriteLine(
                "Checking WorkforceOS device presence..."
            );

            DevicePresenceResponse presence =
                await _presenceClient
                    .GetPresenceAsync(
                        credentials,
                        cancellationToken
                    );

            Console.WriteLine(
                $"Device UUID: {presence.DeviceUuid:D}"
            );

            Console.WriteLine(
                $"Online: {presence.IsOnline}"
            );

            Console.WriteLine(
                $"Online Timeout Seconds: {presence.OnlineTimeoutSeconds}"
            );

            if (
                presence.LastSeenAt is not null
            )
            {
                Console.WriteLine(
                    $"Last Seen: {presence.LastSeenAt:O}"
                );
            }
            else
            {
                Console.WriteLine(
                    "Last Seen: never"
                );
            }

            if (
                presence.OfflineSince is not null
            )
            {
                Console.WriteLine(
                    $"Offline Since: {presence.OfflineSince:O}"
                );
            }

            return 0;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            Console.Error.WriteLine(
                "Operation cancelled."
            );

            return 1;
        }
        catch (
            Exception exception
        )
        when (
            exception
                is WorkforceApiException
                or HttpRequestException
                or InvalidDataException
        )
        {
            Console.Error.WriteLine(
                exception.Message
            );

            return 1;
        }
    }

    // =====================================================
    // LOCAL RESET
    // =====================================================

    private async Task<int> ExecuteResetEnrollmentAsync(
        CancellationToken cancellationToken
    )
    {
        try
        {
            DeviceCredentials? credentials =
                await _enrollmentService
                    .GetCredentialsAsync(
                        cancellationToken
                    );

            if (
                credentials is null
            )
            {
                Console.WriteLine(
                    "No local WorkforceOS enrollment exists."
                );

                return 0;
            }

            Console.WriteLine(
                $"Local Device UUID: {credentials.DeviceUuid:D}"
            );

            Console.WriteLine(
                "This removes local credentials only."
            );

            Console.WriteLine(
                "It does not revoke the device on the WorkforceOS backend."
            );

            Console.Write(
                "Type RESET to continue: "
            );

            string? confirmation =
                Console.ReadLine();

            if (
                !string.Equals(
                    confirmation?.Trim(),
                    "RESET",
                    StringComparison.Ordinal
                )
            )
            {
                Console.WriteLine(
                    "Reset cancelled."
                );

                return 2;
            }

            await _enrollmentService
                .ClearLocalEnrollmentAsync(
                    cancellationToken
                );

            Console.WriteLine(
                "Local WorkforceOS enrollment removed."
            );

            return 0;
        }
        catch (
            OperationCanceledException
        )
        when (
            cancellationToken
                .IsCancellationRequested
        )
        {
            Console.Error.WriteLine(
                "Operation cancelled."
            );

            return 1;
        }
        catch (
            Exception exception
        )
        when (
            exception
                is InvalidDataException
                or IOException
                or UnauthorizedAccessException
        )
        {
            Console.Error.WriteLine(
                $"Unable to reset local enrollment: {exception.Message}"
            );

            return 1;
        }
    }
}