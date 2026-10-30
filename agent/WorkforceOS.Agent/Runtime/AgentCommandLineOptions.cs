namespace WorkforceOS.Agent.Runtime;

public enum AgentCommandMode
{
    RunAgent = 0,
    Enroll = 1,
    Status = 2,
    ResetEnrollment = 3,
    Presence = 4,
    ActivitySessionHelper = 5
}

public sealed record AgentCommandLineOptions
{
    public required AgentCommandMode Mode
    {
        get;
        init;
    }

    public static AgentCommandLineOptions Parse(
        string[] args
    )
    {
        ArgumentNullException.ThrowIfNull(
            args
        );

        bool enrollRequested =
            false;

        bool statusRequested =
            false;

        bool resetEnrollmentRequested =
            false;

        bool presenceRequested =
            false;

        bool activitySessionHelperRequested =
            false;

        foreach (
            string argument
            in args
        )
        {
            if (
                string.Equals(
                    argument,
                    "--enroll",
                    StringComparison.OrdinalIgnoreCase
                )
            )
            {
                enrollRequested =
                    true;

                continue;
            }

            if (
                string.Equals(
                    argument,
                    "--status",
                    StringComparison.OrdinalIgnoreCase
                )
            )
            {
                statusRequested =
                    true;

                continue;
            }

            if (
                string.Equals(
                    argument,
                    "--reset-enrollment",
                    StringComparison.OrdinalIgnoreCase
                )
            )
            {
                resetEnrollmentRequested =
                    true;

                continue;
            }

            if (
                string.Equals(
                    argument,
                    "--presence",
                    StringComparison.OrdinalIgnoreCase
                )
            )
            {
                presenceRequested =
                    true;

                continue;
            }

            if (
                string.Equals(
                    argument,
                    "--activity-session-helper",
                    StringComparison.OrdinalIgnoreCase
                )
            )
            {
                activitySessionHelperRequested =
                    true;
            }
        }

        int requestedModes =
            Convert.ToInt32(
                enrollRequested
            )
            + Convert.ToInt32(
                statusRequested
            )
            + Convert.ToInt32(
                resetEnrollmentRequested
            )
            + Convert.ToInt32(
                presenceRequested
            )
            + Convert.ToInt32(
                activitySessionHelperRequested
            );

        if (
            requestedModes > 1
        )
        {
            throw new ArgumentException(
                "Use only one command mode: --enroll, --status, --presence, --reset-enrollment, or --activity-session-helper."
            );
        }

        if (
            enrollRequested
        )
        {
            return new AgentCommandLineOptions
            {
                Mode =
                    AgentCommandMode.Enroll
            };
        }

        if (
            statusRequested
        )
        {
            return new AgentCommandLineOptions
            {
                Mode =
                    AgentCommandMode.Status
            };
        }

        if (
            resetEnrollmentRequested
        )
        {
            return new AgentCommandLineOptions
            {
                Mode =
                    AgentCommandMode
                        .ResetEnrollment
            };
        }

        if (
            presenceRequested
        )
        {
            return new AgentCommandLineOptions
            {
                Mode =
                    AgentCommandMode.Presence
            };
        }

        if (
            activitySessionHelperRequested
        )
        {
            return new AgentCommandLineOptions
            {
                Mode =
                    AgentCommandMode
                        .ActivitySessionHelper
            };
        }

        return new AgentCommandLineOptions
        {
            Mode =
                AgentCommandMode.RunAgent
        };
    }

    public static string[] GetHostArguments(
        string[] args
    )
    {
        ArgumentNullException.ThrowIfNull(
            args
        );

        return args
            .Where(
                argument =>
                    !IsAgentCommandArgument(
                        argument
                    )
            )
            .ToArray();
    }

    private static bool IsAgentCommandArgument(
        string argument
    )
    {
        return
            string.Equals(
                argument,
                "--enroll",
                StringComparison.OrdinalIgnoreCase
            )
            || string.Equals(
                argument,
                "--status",
                StringComparison.OrdinalIgnoreCase
            )
            || string.Equals(
                argument,
                "--reset-enrollment",
                StringComparison.OrdinalIgnoreCase
            )
            || string.Equals(
                argument,
                "--presence",
                StringComparison.OrdinalIgnoreCase
            )
            || string.Equals(
                argument,
                "--activity-session-helper",
                StringComparison.OrdinalIgnoreCase
            );
    }
}