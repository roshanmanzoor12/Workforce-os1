using System.Text;

namespace WorkforceOS.Agent.Enrollment;

public static class ActivationCodePrompt
{
    private const int MaximumLength =
        256;

    public static string Read()
    {
        if (
            Console.IsInputRedirected
        )
        {
            string? redirectedValue =
                Console.ReadLine();

            return Validate(
                redirectedValue
            );
        }

        Console.Write(
            "Enter WorkforceOS activation code: "
        );

        StringBuilder builder =
            new();

        while (true)
        {
            ConsoleKeyInfo key =
                Console.ReadKey(
                    intercept: true
                );

            if (
                key.Key
                == ConsoleKey.Enter
            )
            {
                Console.WriteLine();

                break;
            }

            if (
                key.Key
                == ConsoleKey.Backspace
            )
            {
                if (
                    builder.Length > 0
                )
                {
                    builder.Length--;
                }

                continue;
            }

            if (
                char.IsControl(
                    key.KeyChar
                )
            )
            {
                continue;
            }

            if (
                builder.Length
                >= MaximumLength
            )
            {
                continue;
            }

            builder.Append(
                key.KeyChar
            );
        }

        return Validate(
            builder.ToString()
        );
    }

    private static string Validate(
        string? value
    )
    {
        if (
            string.IsNullOrWhiteSpace(
                value
            )
        )
        {
            throw new ArgumentException(
                "Activation code is required."
            );
        }

        string normalized =
            value.Trim();

        if (
            normalized.Length < 6
            || normalized.Length > MaximumLength
        )
        {
            throw new ArgumentException(
                "Activation code is invalid."
            );
        }

        return normalized;
    }
}