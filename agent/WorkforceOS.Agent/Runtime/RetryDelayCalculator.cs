namespace WorkforceOS.Agent.Runtime;

public static class RetryDelayCalculator
{
    public static TimeSpan Calculate(
        int consecutiveFailures,
        int initialDelaySeconds,
        int maximumDelaySeconds
    )
    {
        if (
            consecutiveFailures < 1
        )
        {
            consecutiveFailures =
                1;
        }

        if (
            initialDelaySeconds < 1
        )
        {
            initialDelaySeconds =
                1;
        }

        if (
            maximumDelaySeconds
            < initialDelaySeconds
        )
        {
            maximumDelaySeconds =
                initialDelaySeconds;
        }

        int exponent =
            Math.Min(
                consecutiveFailures - 1,
                20
            );

        long multiplier =
            1L << exponent;

        long calculatedSeconds;

        try
        {
            calculatedSeconds =
                checked(
                    (long)initialDelaySeconds
                    * multiplier
                );
        }
        catch (
            OverflowException
        )
        {
            calculatedSeconds =
                maximumDelaySeconds;
        }

        long boundedSeconds =
            Math.Min(
                calculatedSeconds,
                maximumDelaySeconds
            );

        return TimeSpan.FromSeconds(
            boundedSeconds
        );
    }
}